import asyncio
import os
import sys
import json
import logging
import pickle
import tempfile
import re
import subprocess as sp
import time as _time
import psutil
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request as FARequest, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import RedirectResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ptyprocess
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Load core_os modules
try:
    from core_os.skills.auto_lib import model_manager
    from core_os.memory.history import load_shared_history, append_shared_messages
    from core_os.cortex import cortex
except ImportError as e:
    logging.warning(f"Could not import core_os modules: {e}")
    model_manager = None
    cortex = None

try:
    from core_os.skills.skill_manager import (
        install_from_github, install_from_local, execute_skill,
        list_skills, toggle_skill, uninstall_skill, load_all_enabled,
    )
    _skills_available = True
except ImportError as e:
    logging.warning(f"SkillManager unavailable: {e}")
    _skills_available = False

# EasyOCR reader — loaded in background thread at startup (non-blocking)
_ocr_reader = None

app = FastAPI(title="Nexus Forever Morth Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def _preload_ocr():
    import concurrent.futures
    def _load():
        global _ocr_reader
        try:
            import easyocr as _easyocr
            _ocr_reader = _easyocr.Reader(['en'], gpu=False, verbose=False)
            logging.info("EasyOCR reader pre-loaded OK")
        except Exception as _e:
            logging.warning(f"EasyOCR pre-load skipped: {_e}")
    loop = asyncio.get_event_loop()
    loop.run_in_executor(concurrent.futures.ThreadPoolExecutor(max_workers=1), _load)

@app.on_event("startup")
async def _load_skills():
    if _skills_available:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, load_all_enabled)
        logging.info("[SkillManager] All enabled skills loaded.")
    _load_push_tokens()

# --- GLOBAL STATE ---
STATE = {
    "sense": "synesthetic", # synesthetic vs optical
    "active_agents": [],
}

class ChatMessage(BaseModel):
    message: str

class SenseUpdate(BaseModel):
    sense: str

class CommandRequest(BaseModel):
    command: str

class TTSRequest(BaseModel):
    text: str

class ModelRequest(BaseModel):
    model: str

def _strip_for_tts(text: str) -> str:
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)
    text = re.sub(r'[*#_>]', '', text)
    return text.strip()

# --- GOOGLE OAUTH CONFIG ---
CLIENT_SECRETS_FILE = os.path.join(PROJECT_ROOT, "client_secret.json")
TOKEN_PICKLE = os.path.join(PROJECT_ROOT, "token.pickle")
REDIRECT_URI = "http://localhost:8000/api/oauth/callback"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/drive.file",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

# --- API ENDPOINTS ---

@app.get("/api/neuro")
async def get_neuro_state():
    try:
        with open("core_os/memory/neuro_state.json", "r") as f:
            data = json.load(f)
            data["sense"] = STATE["sense"]
            data["google_auth"] = os.path.exists(TOKEN_PICKLE)
            return data
    except Exception:
        return {"dopamine": 0.9, "serotonin": 0.9, "norepinephrine": 0.1, "sense": STATE["sense"], "google_auth": False}

@app.post("/api/sense")
async def update_sense(update: SenseUpdate):
    STATE["sense"] = update.sense
    return {"status": "success", "sense": STATE["sense"]}

@app.get("/api/history")
async def get_history(limit: int = 60):
    """Return persistent chat history for the console."""
    try:
        history = load_shared_history(limit=limit)
        return history
    except Exception as e:
        return []

@app.post("/api/chat")
async def chat_endpoint(chat: ChatMessage):
    if not model_manager:
        return {"response": "[SYSTEM] Milla core offline. Rebuild in progress."}

    def _process():
        """All blocking work in one thread — cortex + model call."""
        cortex_data = {}
        options = {}
        executive_prefix = ""
        if cortex:
            try:
                cortex_data = cortex.process_input(chat.message)
                chems = cortex_data.get("chemicals", {})
                dopamine = chems.get("dopamine", 0.5)
                norep    = chems.get("norepinephrine", 0.2)
                atp      = chems.get("atp_energy", 100.0)
                temp = round(max(0.3, min(1.2, 0.4 + (dopamine * 0.5) - (norep * 0.2) - (max(0, 60 - atp) * 0.003))), 2)
                options = {"temperature": temp}
                instruction = cortex_data.get("executive_instruction", "")
                if instruction:
                    executive_prefix = f"[CORTEX DIRECTIVE: {instruction}] "
            except Exception as e:
                logging.warning(f"[Cortex] Failed: {e}")

        history = load_shared_history(limit=15)
        sense_prompt = f"[Current Sense Active: {STATE['sense'].upper()}] "
        full_message = sense_prompt + executive_prefix + chat.message
        messages = history + [{"role": "user", "content": full_message}]

        response = model_manager.chat(messages=messages, options=options)
        content  = response['message']['content']

        # Strip tool-call JSON wrapping from local models (milla-rayne / qwen)
        try:
            import json as _json
            parsed = _json.loads(content)
            if isinstance(parsed, dict):
                # {"name":"speak_response","arguments":{"text":"..."}}
                text = parsed.get("arguments", {}).get("text") or \
                       parsed.get("text") or \
                       parsed.get("response") or \
                       parsed.get("content")
                if text:
                    content = text
        except Exception:
            pass  # not JSON, leave as-is
        append_shared_messages([
            {"role": "user",      "content": chat.message},
            {"role": "assistant", "content": content},
        ])
        return content, cortex_data

    try:
        loop = asyncio.get_event_loop()
        content, cortex_data = await loop.run_in_executor(None, _process)
        return {
            "response": content,
            "neuro":    cortex_data.get("chemicals", {}),
            "state":    cortex_data.get("state", "HOMEOSTASIS"),
        }
    except Exception as e:
        return {"response": f"[SYSTEM ERROR] {str(e)}"}

# --- GOOGLE OAUTH ROUTES ---

@app.get("/api/oauth/login")
async def oauth_login():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, state = flow.authorization_url(access_type="offline", prompt="consent", include_granted_scopes="true")
    # For a local tool with no session management, we'll bypass state verification by not passing it
    # Google will still use it, but we won't require it back unless we store it.
    return {"url": auth_url}

@app.get("/api/oauth/callback")
async def oauth_callback(request: FARequest):
    try:
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
        
        # Use str(request.url) but replace any 127.0.0.1 with localhost if needed
        full_url = str(request.url).replace("127.0.0.1", "localhost")
        
        # Fetch token WITHOUT state verification for the local dev environment
        flow.fetch_token(authorization_response=full_url)
        
        creds = flow.credentials
        with open(TOKEN_PICKLE, "wb") as f:
            pickle.dump(creds, f)
            
        logging.info("Google OAuth Sync Successful.")
        return RedirectResponse(url="http://localhost:5173/?auth=success")
        
    except Exception as e:
        logging.error(f"OAuth Callback Error: {str(e)}")
        return {"error": f"OAuth Failed: {str(e)}", "help": "Check if http://localhost:8000/api/oauth/callback is in your Google Console Redirect URIs"}

# --- TERMINAL WEBSOCKET ---

@app.websocket("/ws/terminal")
async def websocket_terminal(websocket: WebSocket):
    await websocket.accept()
    pty_env = os.environ.copy()
    pty_env["TERM"] = "xterm-256color"
    child = ptyprocess.PtyProcessUnicode.spawn(['/bin/bash'], env=pty_env, cwd=PROJECT_ROOT)
    
    async def read_from_pty():
        while True:
            try:
                output = await asyncio.get_event_loop().run_in_executor(None, child.read, 1024)
                if output:
                    await websocket.send_text(output)
                else:
                    await asyncio.sleep(0.01)
            except EOFError: break
            except Exception: break

    read_task = asyncio.create_task(read_from_pty())
    try:
        while True:
            data = await websocket.receive_text()
            child.write(data)
    except WebSocketDisconnect: pass
    finally:
        child.terminate(force=True)
        read_task.cancel()

# --- COMMAND ROUTING ---

@app.post("/api/command")
async def command_endpoint(req: CommandRequest):
    cmd = req.command.strip()

    if cmd.startswith("!"):
        shell_cmd = cmd[1:].strip()
        try:
            from core_os.actions import terminal_executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, terminal_executor, shell_cmd)
            return {"output": str(result), "type": "shell"}
        except Exception as e:
            return {"output": f"[Shell Error]: {e}", "type": "shell"}

    elif cmd == "/scan":
        try:
            from core_os.skills.scout import Scout
            scout = Scout(root_path=PROJECT_ROOT)
            issues = scout.hunt()
            if not issues:
                return {"output": "Sector Clear. System Optimal.", "type": "scan", "issues": []}
            formatted = [{"index": i, "label": t["label"], "target": os.path.basename(t["target"]), "details": t["details"]} for i, t in enumerate(issues)]
            return {"output": f"{len(issues)} issues detected.", "type": "scan", "issues": formatted}
        except Exception as e:
            return {"output": f"[Scan Error]: {e}", "type": "scan", "issues": []}

    elif cmd.startswith("/fix"):
        arg = cmd[4:].strip()
        try:
            from core_os.skills.scout import Scout
            scout = Scout(root_path=PROJECT_ROOT)
            issues = scout.hunt()
            if not issues:
                return {"output": "No active issues.", "type": "fix"}
            if arg == "all":
                for t in issues:
                    scout.execute_kill(t)
                return {"output": f"Fixed {len(issues)} issues.", "type": "fix"}
            idx = int(arg)
            scout.execute_kill(issues[idx])
            return {"output": f"Fixed issue {idx}: {issues[idx]['label']}", "type": "fix"}
        except Exception as e:
            return {"output": f"[Fix Error]: {e}", "type": "fix"}

    elif cmd == "/gim":
        try:
            def _run_gim():
                import importlib.util
                spec = importlib.util.spec_from_file_location("milla_gim", os.path.join(PROJECT_ROOT, "milla_gim.py"))
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    return mod.generate_monologue()
                return None
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _run_gim)
            return {"output": result or "GIM cycle complete.", "type": "gim"}
        except Exception as e:
            return {"output": f"[GIM Error]: {e}", "type": "gim"}

    elif cmd.startswith("/model"):
        name = cmd[6:].strip()
        if not name:
            current = model_manager.current_model if model_manager else "offline"
            return {"output": f"Current model: {current}", "type": "model"}
        if model_manager:
            model_manager.switch_model(name)
            return {"output": f"Switched to {name}", "type": "model"}
        return {"output": "[Model] Manager offline.", "type": "model"}

    elif cmd.startswith("/forge ") or cmd.startswith("/makeskill "):
        description = cmd.split(" ", 1)[1].strip()
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, execute_skill, "skill_forge", {"description": description})
            inner = result.get("result", result)
            if inner.get("ok"):
                return {"output": f"✓ Skill '{inner['name']}' created and registered!\nFile: {inner.get('file','')}", "type": "skill"}
            else:
                return {"output": f"[Forge Error]: {inner.get('error','unknown')}", "type": "skill"}
        except Exception as e:
            return {"output": f"[Forge Error]: {e}", "type": "skill"}

    elif cmd.startswith("/skill "):
        parts = cmd[7:].strip().split(None, 1)
        skill_name = parts[0] if parts else ""
        try:
            import json as _json
            payload = _json.loads(parts[1]) if len(parts) > 1 else {}
        except Exception:
            payload = {"input": parts[1]} if len(parts) > 1 else {}
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, execute_skill, skill_name, payload)
            inner = result.get("result", result)
            return {"output": str(inner), "type": "skill"}
        except Exception as e:
            return {"output": f"[Skill Error]: {e}", "type": "skill"}

    return {"output": f"Unknown command: {cmd}. Try /scan /fix /forge /skill /gim /model or !shell", "type": "unknown"}

# --- MODEL SWITCHER ---

@app.get("/api/model")
async def get_model():
    if not model_manager:
        return {"model": "offline", "provider": "none"}
    return {
        "model": model_manager.current_model,
        "provider": model_manager.provider,
        "cloud_host": model_manager.cloud_host or "",
        "cloud_configured": bool(model_manager.cloud_host),
    }

class ProviderRequest(BaseModel):
    provider: str           # "xai" | "ollama" | "ollama_cloud"
    host: str = ""          # required for ollama_cloud
    key: str = ""           # optional bearer key
    model: str = ""         # optional model override

@app.post("/api/model/provider")
async def switch_provider_endpoint(req: ProviderRequest):
    if not model_manager:
        return {"error": "Model manager offline"}
    result = model_manager.switch_provider(req.provider, host=req.host, key=req.key, model=req.model)
    # Persist to .env if cloud host provided
    if req.host and req.provider == "ollama_cloud":
        try:
            env_path = os.path.join(PROJECT_ROOT, ".env")
            lines = open(env_path).readlines() if os.path.exists(env_path) else []
            updated = {l.split("=")[0]: l for l in lines if "=" in l}
            updated["OLLAMA_CLOUD_HOST"] = f"OLLAMA_CLOUD_HOST={req.host}\n"
            if req.key:
                updated["OLLAMA_CLOUD_KEY"] = f"OLLAMA_CLOUD_KEY={req.key}\n"
            if req.model:
                updated["OLLAMA_CLOUD_MODEL"] = f"OLLAMA_CLOUD_MODEL={req.model}\n"
            with open(env_path, "w") as f:
                f.writelines(updated.values())
        except Exception as e:
            logging.warning(f"[Provider] Could not persist .env: {e}")
    return result

@app.get("/api/model/cloud-models")
async def cloud_models():
    """Return list of popular Ollama cloud models."""
    try:
        from core_os.skills.auto_lib import OLLAMA_CLOUD_MODELS
        return {"models": OLLAMA_CLOUD_MODELS}
    except Exception:
        return {"models": []}

@app.get("/api/model/local-models")
async def local_models():
    """Return locally installed Ollama models."""
    try:
        result = ollama_list() if (m := __import__("ollama", fromlist=["list"])) else None
        models = [{"id": m["model"], "name": m["model"], "size": m.get("size", 0)}
                  for m in (result.get("models", []) if result else [])]
        return {"models": models}
    except Exception:
        import subprocess
        try:
            out = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            lines = [l.strip() for l in out.stdout.splitlines()[1:] if l.strip()]
            return {"models": [{"id": l.split()[0], "name": l.split()[0]} for l in lines]}
        except Exception:
            return {"models": []}

@app.post("/api/model")
async def switch_model_endpoint(req: ModelRequest):
    if not model_manager:
        return {"error": "Model manager offline"}
    model_manager.switch_model(req.model)
    return {"model": req.model, "status": "switched"}

# --- TTS ---

@app.post("/api/tts")
async def tts_endpoint(req: TTSRequest, background_tasks: BackgroundTasks):
    import edge_tts
    text = _strip_for_tts(req.text)
    if not text:
        return {"error": "Empty text"}
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    try:
        communicate = edge_tts.Communicate(text, "en-US-AvaNeural", pitch="-5Hz", rate="-5%")
        await communicate.save(tmp.name)
        background_tasks.add_task(os.unlink, tmp.name)
        return FileResponse(tmp.name, media_type="audio/mpeg", filename="speech.mp3")
    except Exception as e:
        os.unlink(tmp.name)
        return {"error": str(e)}

# --- STT ---

@app.post("/api/stt")
async def stt_endpoint(audio: UploadFile = File(...)):
    import shutil
    suffix = ".webm"
    if audio.filename and "." in audio.filename:
        suffix = "." + audio.filename.rsplit(".", 1)[1]
    tmp_in = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    wav_path = tmp_in.name.replace(suffix, ".wav")
    try:
        shutil.copyfileobj(audio.file, tmp_in)
        tmp_in.close()
        sp.run(
            ["ffmpeg", "-i", tmp_in.name, "-ac", "1", "-ar", "16000", wav_path, "-y", "-hide_banner", "-loglevel", "error"],
            capture_output=True
        )
        from faster_whisper import WhisperModel
        wmodel = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = wmodel.transcribe(wav_path, beam_size=5)
        transcript = " ".join(s.text for s in segments).strip()
        return {"transcript": transcript}
    except Exception as e:
        return {"transcript": "", "error": str(e)}
    finally:
        for p in [tmp_in.name, wav_path]:
            try:
                if os.path.exists(p):
                    os.unlink(p)
            except Exception:
                pass

# --- NODE STATUS ---

@app.get("/api/nodes")
async def nodes_status():
    tablet_ip = os.getenv("TABLET_IP", "192.168.40.115:34213")
    termux_online = False
    try:
        result = sp.run(["adb", "devices"], capture_output=True, text=True, timeout=3)
        termux_online = tablet_ip in result.stdout
    except Exception:
        pass
    return {
        "termux": termux_online,
        "google": os.path.exists(TOKEN_PICKLE),
        "swarm": len(STATE.get("active_agents", [])) > 0,
    }

# ---------------------------------------------------------------------------
# AGENT SWARM CONTROL
# ---------------------------------------------------------------------------

_SWARM_AGENTS = [
    {"id": "security",    "name": "Security Agent",         "script": "core_os/agents/security_agent/security_agent.py",               "schedule": "every 3h",  "type": "security"},
    {"id": "investigate", "name": "Investigative Agent",    "script": "core_os/agents/investigative_agent/investigative_agent.py",      "schedule": "every 3h",  "type": "security"},
    {"id": "network",     "name": "Network Security Agent", "script": "core_os/agents/network_security_agent/network_security_agent.py","schedule": "every 3h",  "type": "security"},
    {"id": "judge",       "name": "Judge Agent",            "script": "core_os/agents/judge_agent/judge_agent.py",                      "schedule": "on-demand", "type": "security"},
    {"id": "360",         "name": "360° Correlation Agent", "script": "core_os/agents/360_agent/360_agent.py",                          "schedule": "every 3h",  "type": "analysis"},
    {"id": "coding",      "name": "Coding Agent",           "script": "core_os/agents/coding_agent/run_coding.py",                      "schedule": "every 30m", "type": "dev"},
    {"id": "research",    "name": "Research Agent",         "script": "core_os/agents/research_agent/run_research.py",                  "schedule": "every 30m", "type": "dev"},
    {"id": "utility",     "name": "Utility Agent",          "script": "core_os/agents/utility_agent/run_utility.py",                    "schedule": "every 30m", "type": "dev"},
    {"id": "librarian",   "name": "Librarian Twins",        "script": "core_os/agents/librarian_agent.py",                              "schedule": "on-demand", "type": "memory"},
    {"id": "dialogue",    "name": "Dialogue Analyst",       "script": "core_os/agents/dialogue_analyst_agent/dialogue_analyst.py",      "schedule": "on-demand", "type": "analysis"},
]

_SWARM_LOG = os.path.join(os.path.expanduser("~"), "security_data", "cron.log")
_FLAGS_FILE = os.path.join(os.path.expanduser("~"), "security_data", "security_flags.json")
_REPORT_DIR = os.path.join(os.path.expanduser("~"), "security_data", "reports")
_RUNNING_PROCS: dict = {}  # agent_id -> subprocess.Popen


def _agent_running(agent_id: str) -> bool:
    proc = _RUNNING_PROCS.get(agent_id)
    return proc is not None and proc.poll() is None


def _agent_last_run(agent_id: str) -> str:
    """Scan cron log for last run timestamp of an agent."""
    try:
        if not os.path.exists(_SWARM_LOG):
            return "never"
        lines = Path(_SWARM_LOG).read_text(errors="replace").splitlines()
        # Search backwards for this agent's script name
        script_hint = agent_id
        for line in reversed(lines):
            if script_hint in line.lower() or "is up and running" in line.lower():
                # Try to get timestamp from log if prefixed
                return line[:19] if len(line) > 19 else "recently"
        return "never"
    except Exception:
        return "unknown"


@app.get("/api/swarm/status")
async def swarm_status():
    """Return status of all swarm agents."""
    os.makedirs(os.path.dirname(_FLAGS_FILE), exist_ok=True)
    agents_out = []
    for ag in _SWARM_AGENTS:
        running = _agent_running(ag["id"])
        agents_out.append({**ag, "running": running, "last_run": _agent_last_run(ag["id"])})

    # Load latest flags summary
    flags = []
    try:
        if os.path.exists(_FLAGS_FILE):
            flags = json.loads(Path(_FLAGS_FILE).read_text())
    except Exception:
        pass

    # Load latest report if any
    latest_report = None
    try:
        reports = sorted(Path(_REPORT_DIR).glob("*.json")) if os.path.isdir(_REPORT_DIR) else []
        if reports:
            latest_report = json.loads(reports[-1].read_text())
    except Exception:
        pass

    return {
        "ok": True,
        "agents": agents_out,
        "flags_count": len(flags),
        "flags_recent": flags[-5:] if flags else [],
        "latest_report": latest_report,
        "swarm_active": any(_agent_running(ag["id"]) for ag in _SWARM_AGENTS),
    }


class SwarmDispatch(BaseModel):
    agent_id: str
    payload: dict = {}


@app.post("/api/swarm/dispatch")
async def swarm_dispatch(req: SwarmDispatch):
    """Manually trigger an agent to run now."""
    ag = next((a for a in _SWARM_AGENTS if a["id"] == req.agent_id), None)
    if not ag:
        raise HTTPException(status_code=404, detail=f"Agent '{req.agent_id}' not found")
    if _agent_running(req.agent_id):
        return {"ok": False, "message": f"{ag['name']} is already running"}

    script_path = os.path.join(PROJECT_ROOT, ag["script"])
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail=f"Script not found: {ag['script']}")

    # Write task payload for agents that support it
    if req.payload:
        data_dir = os.path.expanduser("~/security_data")
        os.makedirs(data_dir, exist_ok=True)
        task_file_map = {
            "coding":   os.path.join(str(PROJECT_ROOT), "security_data", "coding_tasks.json"),
            "research": os.path.join(str(PROJECT_ROOT), "security_data", "research_tasks.json"),
            "utility":  os.path.join(str(PROJECT_ROOT), "security_data", "utility_tasks.json"),
        }
        if req.agent_id in task_file_map:
            tf = task_file_map[req.agent_id]
            existing = []
            try:
                if os.path.exists(tf):
                    existing = json.loads(Path(tf).read_text())
            except Exception:
                pass
            existing.append({**req.payload, "status": "pending", "created": _time.time()})
            Path(tf).write_text(json.dumps(existing, indent=2))

    log_path = _SWARM_LOG
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
    with open(log_path, "a") as lf:
        proc = sp.Popen(
            [sys.executable, script_path],
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=lf, stderr=lf
        )
    _RUNNING_PROCS[req.agent_id] = proc
    STATE.setdefault("active_agents", [])
    if req.agent_id not in STATE["active_agents"]:
        STATE["active_agents"].append(req.agent_id)
    return {"ok": True, "message": f"{ag['name']} launched (PID {proc.pid})"}


@app.post("/api/swarm/dispatch_all")
async def swarm_dispatch_all():
    """Launch all security agents in sequence."""
    launched = []
    for ag in _SWARM_AGENTS:
        if ag["type"] == "security" and not _agent_running(ag["id"]):
            result = await swarm_dispatch(SwarmDispatch(agent_id=ag["id"]))
            if result.get("ok"):
                launched.append(ag["name"])
    return {"ok": True, "launched": launched}


@app.get("/api/swarm/flags")
async def swarm_flags(limit: int = 50):
    """Return latest security flags."""
    try:
        if not os.path.exists(_FLAGS_FILE):
            return {"ok": True, "flags": [], "count": 0}
        flags = json.loads(Path(_FLAGS_FILE).read_text())
        return {"ok": True, "flags": flags[-limit:], "count": len(flags)}
    except Exception as e:
        return {"ok": False, "error": str(e), "flags": []}


@app.delete("/api/swarm/flags")
async def swarm_clear_flags():
    """Clear all security flags."""
    try:
        Path(_FLAGS_FILE).write_text("[]")
        return {"ok": True, "message": "Flags cleared"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/swarm/log")
async def swarm_log(lines: int = 100):
    """Tail the swarm activity log."""
    try:
        if not os.path.exists(_SWARM_LOG):
            return {"ok": True, "log": "No activity yet."}
        content = Path(_SWARM_LOG).read_text(errors="replace")
        tail = "\n".join(content.strip().splitlines()[-lines:])
        return {"ok": True, "log": tail}
    except Exception as e:
        return {"ok": False, "error": str(e), "log": ""}

# --- OCR ---

@app.post("/api/ocr")
async def ocr_endpoint():
    try:
        from core_os.skills.milla_vision import capture_frame
        frame_path = capture_frame()
        if not frame_path:
            return {"text": "", "error": "No visual input available (no USB cam, tablet, or display)"}
        reader = _ocr_reader
        if reader is None:
            import easyocr
            reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        results = reader.readtext(frame_path)
        text = "\n".join(r[1] for r in results)
        return {"text": text}
    except Exception as e:
        return {"text": "", "error": str(e)}


# ── Computer Use ──────────────────────────────────────────────────────────────
class ComputerActionRequest(BaseModel):
    action: str
    args: dict = {}

class HeadlessRequest(BaseModel):
    headless: bool

@app.post("/api/computer/browser/headless")
async def set_browser_headless(req: HeadlessRequest):
    """Toggle Playwright browser headless mode (restarts browser on next use)."""
    from core_os.skills.computer_use import set_headless, close_browser
    close_browser()  # force re-launch with new mode on next call
    set_headless(req.headless)
    return {"headless": req.headless, "status": "Browser will relaunch in selected mode on next use"}

@app.post("/api/computer/action")
async def computer_single_action(req: ComputerActionRequest):
    """Execute a single computer action (click, type, key, shell, browser_*, etc.)"""
    try:
        from core_os.skills.computer_use import execute_action
        result = await asyncio.get_event_loop().run_in_executor(
            None, execute_action, {"action": req.action, "args": req.args}
        )
        return {"result": result, "action": req.action}
    except Exception as e:
        return {"error": str(e), "action": req.action}

@app.get("/api/computer/run")
async def computer_run_agent(task: str, max_steps: int = 20):
    """
    SSE stream — runs the Grok-4 vision agentic loop.
    Each event is a JSON step dict.
    """
    from core_os.skills.computer_use_agent import run_agent

    def _event_stream():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(lambda: list(run_agent(task, max_steps)))
            steps = future.result(timeout=300)
        for step in steps:
            yield f"data: {json.dumps(step)}\n\n"
        yield "data: [DONE]\n\n"

    # Run synchronously in thread to avoid blocking event loop during vision calls
    async def _async_stream():
        loop = asyncio.get_event_loop()
        steps_future = loop.run_in_executor(None, lambda: list(run_agent(task, max_steps)))
        steps = await steps_future
        for step in steps:
            yield f"data: {json.dumps(step)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        _async_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


# ── Macro endpoints ───────────────────────────────────────────────────────────
class MacroRecordRequest(BaseModel):
    name: str

class MacroPlayRequest(BaseModel):
    name: str
    delay: float = 0.15

@app.post("/api/computer/macro/record/start")
async def macro_start(req: MacroRecordRequest):
    from core_os.skills.computer_macro import start_recording
    return {"status": start_recording(req.name)}

@app.post("/api/computer/macro/record/stop")
async def macro_stop():
    from core_os.skills.computer_macro import stop_recording
    return {"status": stop_recording()}

@app.get("/api/computer/macro/list")
async def macro_list():
    from core_os.skills.computer_macro import list_macros
    return {"macros": list_macros()}

@app.post("/api/computer/macro/play")
async def macro_play(req: MacroPlayRequest):
    from core_os.skills.computer_macro import play_macro
    results = await asyncio.get_event_loop().run_in_executor(
        None, play_macro, req.name, req.delay
    )
    return {"name": req.name, "results": results}

@app.delete("/api/computer/macro/{name}")
async def macro_delete(name: str):
    from core_os.skills.computer_macro import delete_macro
    return {"status": delete_macro(name)}

@app.get("/api/computer/macro/status")
async def macro_status():
    from core_os.skills.computer_macro import recording_status
    return recording_status()

# ── Screenshot with optional region ──────────────────────────────────────────
@app.get("/api/computer/screenshot")
async def computer_screenshot(scale: float = 0.5, x: int = 0, y: int = 0, w: int = 0, h: int = 0):
    """Return a base64 screenshot, optionally cropped to a region."""
    import tempfile, subprocess as _sp, base64 as _b64
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    env = {**os.environ, "DISPLAY": os.getenv("DISPLAY", ":0.0")}
    try:
        _sp.run(["gnome-screenshot", "-f", path], timeout=5, check=True, env=env)
    except Exception:
        _sp.run(["import", "-window", "root", path], timeout=5, check=True, env=env)
    if w > 0 and h > 0:
        cropped = path.replace(".png", "_c.png")
        _sp.run(["convert", path, "-crop", f"{w}x{h}+{x}+{y}", "+repage", cropped], timeout=5)
        if os.path.exists(cropped):
            os.unlink(path)
            path = cropped
    if scale < 1.0:
        scaled = path.replace(".png", "_s.png")
        _sp.run(["convert", path, "-resize", f"{int(scale*100)}%", scaled], timeout=5)
        if os.path.exists(scaled):
            os.unlink(path)
            path = scaled
    with open(path, "rb") as f:
        b64 = _b64.b64encode(f.read()).decode()
    os.unlink(path)
    return {"screenshot": b64}


# ---------------------------------------------------------------------------
# SKILL MANAGER ROUTES
# ---------------------------------------------------------------------------

class SkillInstallRequest(BaseModel):
    url: str           # GitHub URL or user/repo/path.py

class SkillRunRequest(BaseModel):
    payload: dict = {}

class SkillToggleRequest(BaseModel):
    enabled: bool

@app.get("/api/skills")
async def api_list_skills():
    if not _skills_available:
        return {"skills": [], "error": "SkillManager not loaded"}
    return {"skills": list_skills()}

@app.post("/api/skills/install")
async def api_install_skill(req: SkillInstallRequest):
    if not _skills_available:
        return {"ok": False, "message": "SkillManager not loaded"}
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, install_from_github, req.url)
    return result

@app.post("/api/skills/{name}/run")
async def api_run_skill(name: str, req: SkillRunRequest):
    if not _skills_available:
        return {"ok": False, "error": "SkillManager not loaded"}
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, execute_skill, name, req.payload)
    return result

@app.put("/api/skills/{name}/toggle")
async def api_toggle_skill(name: str, req: SkillToggleRequest):
    if not _skills_available:
        return {"ok": False, "error": "SkillManager not loaded"}
    return toggle_skill(name, req.enabled)

@app.delete("/api/skills/{name}")
async def api_uninstall_skill(name: str):
    if not _skills_available:
        return {"ok": False, "error": "SkillManager not loaded"}
    return uninstall_skill(name)


# ---------------------------------------------------------------------------
# MOBILE — WebSocket neuro stream, voice pipeline, push notifications
# ---------------------------------------------------------------------------

# Registered push tokens: {token: {"platform": "ios"|"android", "registered_at": ...}}
_push_tokens: dict = {}
_PUSH_TOKENS_PATH = os.path.join(PROJECT_ROOT, "core_os", "memory", "push_tokens.json")

def _load_push_tokens():
    global _push_tokens
    try:
        if os.path.exists(_PUSH_TOKENS_PATH):
            with open(_PUSH_TOKENS_PATH, "r") as f:
                _push_tokens = json.load(f)
    except Exception as e:
        logging.warning(f"[Push] Could not load tokens: {e}")

def _save_push_tokens():
    try:
        with open(_PUSH_TOKENS_PATH, "w") as f:
            json.dump(_push_tokens, f)
    except Exception as e:
        logging.warning(f"[Push] Could not save tokens: {e}")

class DeviceRegisterRequest(BaseModel):
    token: str
    platform: str = "android"

class PushNotifyRequest(BaseModel):
    title: str
    body: str
    data: dict = {}

@app.post("/api/devices/register")
async def register_device(req: DeviceRegisterRequest):
    """Register an Expo push token for Milla notifications."""
    import datetime
    _push_tokens[req.token] = {"platform": req.platform, "registered_at": datetime.datetime.utcnow().isoformat()}
    _save_push_tokens()
    logging.info(f"[Mobile] Device registered: {req.token[:20]}… ({req.platform})")
    return {"ok": True, "registered": len(_push_tokens)}

@app.post("/api/notify")
async def send_push(req: PushNotifyRequest):
    """Send push notification to all registered devices via Expo Push API."""
    if not _push_tokens:
        return {"ok": False, "message": "No devices registered"}
    import httpx
    messages = [{"to": token, "sound": "default", "title": req.title, "body": req.body, "data": req.data}
                for token in _push_tokens]
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post("https://exp.host/--/api/v2/push/send",
                                     json=messages, timeout=10)
        return {"ok": True, "sent": len(messages), "response": resp.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.websocket("/ws/neuro")
async def ws_neuro(websocket: WebSocket):
    """Stream neuro state to mobile every 2 seconds."""
    await websocket.accept()
    try:
        while True:
            try:
                with open("core_os/memory/neuro_state.json", "r") as f:
                    state = json.load(f)
                state["sense"] = STATE.get("sense", "default")
            except Exception:
                state = {}
            await websocket.send_json(state)
            await asyncio.sleep(2)
    except (WebSocketDisconnect, Exception):
        pass

@app.websocket("/ws/voice")
async def ws_voice(websocket: WebSocket):
    """
    Voice pipeline WebSocket:
      client → sends raw PCM audio chunks (bytes)
      server → STT → Milla chat → TTS → sends back MP3 audio (bytes)
              also sends JSON status frames: {"type":"transcript","text":"..."}
    """
    await websocket.accept()
    audio_buf = bytearray()

    async def _process_audio(pcm_data: bytes) -> str:
        """Convert PCM → WAV → Whisper STT."""
        import tempfile, subprocess as _sp
        with tempfile.NamedTemporaryFile(suffix=".pcm", delete=False) as f:
            f.write(pcm_data); pcm_path = f.name
        wav_path = pcm_path.replace(".pcm", ".wav")
        _sp.run(["ffmpeg", "-y", "-f", "s16le", "-ar", "16000", "-ac", "1",
                 "-i", pcm_path, wav_path], capture_output=True, timeout=10)
        os.unlink(pcm_path)
        # STT via local Whisper (ollama) or fallback to /api/stt logic
        try:
            import whisper as _whisper
            model = _whisper.load_model("base")
            result = model.transcribe(wav_path)
            os.unlink(wav_path)
            return result.get("text", "").strip()
        except Exception:
            pass
        # Fallback: use faster_whisper if available
        try:
            from faster_whisper import WhisperModel
            wm = WhisperModel("tiny", device="cpu", compute_type="int8")
            segs, _ = wm.transcribe(wav_path)
            os.unlink(wav_path)
            return " ".join(s.text for s in segs).strip()
        except Exception:
            pass
        os.unlink(wav_path)
        return ""

    try:
        while True:
            msg = await websocket.receive()
            if "bytes" in msg and msg["bytes"]:
                audio_buf.extend(msg["bytes"])
                # End-of-utterance marker: client sends empty bytes frame
                if len(msg["bytes"]) == 0 and audio_buf:
                    pcm = bytes(audio_buf); audio_buf.clear()
                    loop = asyncio.get_event_loop()

                    # STT
                    transcript = await loop.run_in_executor(None, lambda: asyncio.run(_process_audio(pcm)))
                    if not transcript:
                        await websocket.send_json({"type": "error", "text": "Could not transcribe audio"})
                        continue

                    await websocket.send_json({"type": "transcript", "text": transcript})

                    # Milla response
                    if model_manager:
                        history = load_shared_history(limit=10)
                        messages = history + [{"role": "user", "content": transcript}]
                        resp = await loop.run_in_executor(None, lambda: model_manager.chat(messages=messages))
                        reply = resp["message"]["content"]
                        append_shared_messages([{"role": "user", "content": transcript},
                                                {"role": "assistant", "content": reply}])
                        await websocket.send_json({"type": "response", "text": reply})

                        # TTS → send audio back
                        try:
                            import tempfile, edge_tts
                            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
                                tts_path = tf.name
                            comm = edge_tts.Communicate(reply, "en-US-AvaNeural", rate="-8%", pitch="-2Hz")
                            await comm.save(tts_path)
                            with open(tts_path, "rb") as f:
                                audio_data = f.read()
                            os.unlink(tts_path)
                            await websocket.send_bytes(audio_data)
                        except Exception as e:
                            await websocket.send_json({"type": "tts_error", "text": str(e)})

            elif "text" in msg:
                # Text message — treat as direct chat (typed on mobile)
                text = msg["text"].strip()
                if text and model_manager:
                    loop = asyncio.get_event_loop()
                    history = load_shared_history(limit=10)
                    messages = history + [{"role": "user", "content": text}]
                    resp = await loop.run_in_executor(None, lambda: model_manager.chat(messages=messages))
                    reply = resp["message"]["content"]
                    append_shared_messages([{"role": "user", "content": text},
                                            {"role": "assistant", "content": reply}])
                    await websocket.send_json({"type": "response", "text": reply})

    except (WebSocketDisconnect, Exception) as e:
        logging.info(f"[VoiceWS] disconnected: {e}")


# ---------------------------------------------------------------------------
# CAST / CHROMECAST
# ---------------------------------------------------------------------------
try:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "core_os", "tools"))
    import cast_control as _cast
    _cast_available = True
except ImportError:
    _cast_available = False
    logging.warning("[Cast] pychromecast not available — cast routes disabled")

class CastYouTubeRequest(BaseModel):
    video_id: str
    device_name: str = ""
    ip: str = ""

class CastVolumeRequest(BaseModel):
    level: float   # 0.0 – 1.0
    device_name: str = ""
    ip: str = ""

@app.get("/api/cast/discover")
async def cast_discover():
    if not _cast_available:
        return {"ok": False, "error": "pychromecast not installed"}
    loop = asyncio.get_event_loop()
    try:
        devices = await loop.run_in_executor(None, _cast.discover_casts)
        return {"ok": True, "devices": devices}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/cast/youtube")
async def cast_youtube(req: CastYouTubeRequest):
    if not _cast_available:
        return {"ok": False, "error": "pychromecast not installed"}
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, lambda: _cast.play_youtube(
            req.device_name, req.video_id, ip=req.ip or None))
        return {"ok": True, "video_id": req.video_id}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/cast/volume")
async def cast_volume(req: CastVolumeRequest):
    if not _cast_available:
        return {"ok": False, "error": "pychromecast not installed"}
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, lambda: _cast.set_volume(
            req.device_name, req.level, ip=req.ip or None))
        return {"ok": True, "level": req.level}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# GOOGLE CALENDAR
# ---------------------------------------------------------------------------
try:
    from core_os.skills.google_calendar import fetch_upcoming_events, list_calendars, TOKEN_FILE as _CAL_TOKEN_FILE
    _calendar_available = True
except ImportError:
    _calendar_available = False
    _CAL_TOKEN_FILE = ""
    logging.warning("[Calendar] google_calendar skill not available")

def _calendar_authorized() -> bool:
    """Return True only if a valid calendar token exists (avoids blocking OAuth flow)."""
    return bool(_CAL_TOKEN_FILE) and os.path.exists(_CAL_TOKEN_FILE)

@app.get("/api/calendar/today")
async def calendar_today():
    if not _calendar_available:
        return {"ok": False, "error": "Calendar skill not available"}
    if not _calendar_authorized():
        return {"ok": False, "error": "Not authorized — visit /api/oauth/login to connect Google"}
    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(loop.run_in_executor(None, lambda: fetch_upcoming_events(days=1)), timeout=10)
        return {"ok": True, **result}
    except asyncio.TimeoutError:
        return {"ok": False, "error": "Calendar request timed out"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/calendar/week")
async def calendar_week():
    if not _calendar_available:
        return {"ok": False, "error": "Calendar skill not available"}
    if not _calendar_authorized():
        return {"ok": False, "error": "Not authorized — visit /api/oauth/login to connect Google"}
    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(loop.run_in_executor(None, lambda: fetch_upcoming_events(days=7)), timeout=10)
        return {"ok": True, **result}
    except asyncio.TimeoutError:
        return {"ok": False, "error": "Calendar request timed out"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# CRON MANAGER
# ---------------------------------------------------------------------------
import shlex

_CRON_JOBS = [
    {"id": "gim",       "name": "GIM (Internal Monologue)", "schedule": "0 6,12,18,0 * * *",
     "script": "milla_gim.py",           "log": "milla_cron.log",         "cwd": PROJECT_ROOT},
    {"id": "email",     "name": "Email Responder",           "schedule": "*/10 * * * *",
     "script": "milla_email_cron.py",    "log": "milla_email_cron.log",   "cwd": PROJECT_ROOT},
    {"id": "telegram",  "name": "Telegram Relay",            "schedule": "*/2 * * * *",
     "script": "milla_telegram_relay.py","log": "milla_telegram.log",     "cwd": os.path.join(PROJECT_ROOT, "RAYNE_Admin")},
    {"id": "brief",     "name": "Daily Brief",               "schedule": "5 0 * * *",
     "script": "milla_daily_brief.py",   "log": "milla_cron.log",         "cwd": PROJECT_ROOT},
    {"id": "upgrade",   "name": "Upgrade Search",            "schedule": "0 0 */2 * *",
     "script": "milla_upgrade_search.py","log": "milla_cron.log",         "cwd": PROJECT_ROOT},
    {"id": "device",    "name": "Device Link",               "schedule": "*/5 * * * *",
     "script": "milla_device_link.py",   "log": "milla_device.log",       "cwd": PROJECT_ROOT},
    {"id": "heartbeat", "name": "Connection Heartbeat",      "schedule": "0 0,6,12,18 * * *",
     "script": "core_os/scripts/milla_heartbeat.py", "log": "milla_cron.log", "cwd": PROJECT_ROOT},
    {"id": "dream",     "name": "Dream Cycle (REM)",         "schedule": "0 2 * * *",
     "script": "milla_dream.py",         "log": "milla_cron.log",         "cwd": PROJECT_ROOT},
    {"id": "backup",    "name": "Database Backup",           "schedule": "0 */6 * * *",
     "script": None,                     "log": "milla_cron.log",         "cwd": PROJECT_ROOT,
     "cmd": "rsync -a --update core_os/memory/milla_long_term.db core_os/memory/agent_memory.db /home/nexus/milla_backups/"},
]
_VENV_PYTHON = os.path.join(PROJECT_ROOT, "venv", "bin", "python3")

def _cron_log_tail(log_file: str, lines: int = 30) -> str:
    path = os.path.join(PROJECT_ROOT, log_file)
    if not os.path.exists(path):
        return ""
    try:
        result = sp.run(["tail", f"-{lines}", path], capture_output=True, text=True, timeout=5)
        return result.stdout
    except Exception:
        return ""

@app.get("/api/cron/list")
async def cron_list():
    jobs = []
    for job in _CRON_JOBS:
        log_snippet = _cron_log_tail(job["log"], 5)
        jobs.append({
            "id": job["id"],
            "name": job["name"],
            "schedule": job["schedule"],
            "script": job.get("script") or "[rsync]",
            "log_tail": log_snippet,
        })
    return {"ok": True, "jobs": jobs}

class CronTriggerRequest(BaseModel):
    job_id: str

@app.post("/api/cron/trigger")
async def cron_trigger(req: CronTriggerRequest):
    job = next((j for j in _CRON_JOBS if j["id"] == req.job_id), None)
    if not job:
        return {"ok": False, "error": f"Unknown job: {req.job_id}"}
    loop = asyncio.get_event_loop()
    def _run():
        cwd = job["cwd"]
        if job.get("script"):
            script_path = os.path.join(cwd if cwd == PROJECT_ROOT else PROJECT_ROOT, job["script"])
            cmd = [_VENV_PYTHON, job["script"]]
        else:
            cmd = shlex.split(job["cmd"])
        log_path = os.path.join(PROJECT_ROOT, job["log"])
        with open(log_path, "a") as lf:
            proc = sp.Popen(cmd, cwd=cwd, stdout=lf, stderr=lf)
            proc.wait(timeout=60)
        return proc.returncode
    try:
        rc = await loop.run_in_executor(None, _run)
        return {"ok": True, "job_id": req.job_id, "exit_code": rc}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/cron/{job_id}/logs")
async def cron_logs(job_id: str, lines: int = 50):
    job = next((j for j in _CRON_JOBS if j["id"] == job_id), None)
    if not job:
        return {"ok": False, "error": "Unknown job"}
    return {"ok": True, "log": _cron_log_tail(job["log"], lines)}


# ---------------------------------------------------------------------------
# MEMORY BROWSER
# ---------------------------------------------------------------------------
_MEMORY_DB = os.path.join(PROJECT_ROOT, "core_os", "memory", "milla_long_term.db")

@app.get("/api/memory/search")
async def memory_search(q: str = "", limit: int = 30, offset: int = 0):
    import sqlite3
    try:
        conn = sqlite3.connect(_MEMORY_DB)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if q.strip():
            rows = cur.execute(
                "SELECT rowid, fact, category, topic FROM memories WHERE memories MATCH ? LIMIT ? OFFSET ?",
                (q.strip(), limit, offset)
            ).fetchall()
        else:
            rows = cur.execute(
                "SELECT rowid, fact, category, topic FROM memories LIMIT ? OFFSET ?",
                (limit, offset)
            ).fetchall()
        total = cur.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        conn.close()
        return {"ok": True, "total": total, "memories": [dict(r) for r in rows]}
    except Exception as e:
        return {"ok": False, "error": str(e), "memories": []}

@app.delete("/api/memory/{rowid}")
async def memory_delete(rowid: int):
    import sqlite3
    try:
        conn = sqlite3.connect(_MEMORY_DB)
        conn.execute("DELETE FROM memories WHERE rowid = ?", (rowid,))
        conn.commit()
        conn.close()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

class MemoryAddRequest(BaseModel):
    fact: str
    category: str = "manual"
    topic: str = "user-added"

@app.post("/api/memory")
async def memory_add(req: MemoryAddRequest):
    import sqlite3
    try:
        conn = sqlite3.connect(_MEMORY_DB)
        conn.execute(
            "INSERT INTO memories(fact, category, topic, is_genesis_era, is_historical_log) VALUES (?,?,?,0,0)",
            (req.fact.strip(), req.category, req.topic)
        )
        conn.commit()
        conn.close()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ---------------------------------------------------------------------------
# AGENT ACTIVITY FEED
# ---------------------------------------------------------------------------
_FEED_SOURCES = [
    {"label": "Dreams", "path": "core_os/memory/dreams.txt", "type": "text"},
    {"label": "Stream", "path": "core_os/memory/stream_of_consciousness.md", "type": "text"},
    {"label": "Upgrade Radar", "path": "core_os/memory/upgrade_radar.md", "type": "text"},
    {"label": "Last Error", "path": "core_os/memory/last_error.txt", "type": "text"},
]

@app.get("/api/agent/feed")
async def agent_feed(lines: int = 60):
    items = []
    # Cron log tails
    for job in _CRON_JOBS:
        tail = _cron_log_tail(job["log"], 8)
        if tail.strip():
            items.append({"source": f"cron:{job['name']}", "content": tail, "job_id": job["id"]})
    # Memory/log files
    for src in _FEED_SOURCES:
        full = os.path.join(PROJECT_ROOT, src["path"])
        if os.path.exists(full):
            try:
                with open(full, "r", errors="replace") as f:
                    content = f.read()
                # Take last N lines
                last_lines = "\n".join(content.strip().splitlines()[-lines:])
                if last_lines.strip():
                    items.append({"source": src["label"], "content": last_lines})
            except Exception:
                pass
    return {"ok": True, "feed": items}

# ---------------------------------------------------------------------------
# PERSONA EDITOR
# ---------------------------------------------------------------------------
_PERSONA_OVERRIDE_PATH = os.path.join(PROJECT_ROOT, "core_os", "memory", "persona_override.txt")

class PersonaUpdateRequest(BaseModel):
    prompt: str

@app.get("/api/persona")
async def persona_get():
    # Return override if exists, else the compiled-in prompt
    if os.path.exists(_PERSONA_OVERRIDE_PATH):
        with open(_PERSONA_OVERRIDE_PATH, "r") as f:
            prompt = f.read()
    else:
        from core_os.skills.auto_lib import MILLA_SYSTEM_PROMPT
        prompt = MILLA_SYSTEM_PROMPT
    return {"ok": True, "prompt": prompt, "is_override": os.path.exists(_PERSONA_OVERRIDE_PATH)}

@app.post("/api/persona")
async def persona_update(req: PersonaUpdateRequest):
    try:
        with open(_PERSONA_OVERRIDE_PATH, "w") as f:
            f.write(req.prompt)
        # Hot-reload model manager system prompt
        if model_manager:
            model_manager.system_prompt_override = req.prompt
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.delete("/api/persona")
async def persona_reset():
    if os.path.exists(_PERSONA_OVERRIDE_PATH):
        os.unlink(_PERSONA_OVERRIDE_PATH)
    if model_manager:
        model_manager.system_prompt_override = None
    return {"ok": True, "message": "Persona reset to default"}


# ---------------------------------------------------------------------------
# GMAIL / EMAIL
# ---------------------------------------------------------------------------
def _gmail_authorized() -> bool:
    try:
        from core_os.skills.auto_lib import authenticate_gmail
        svc = authenticate_gmail()
        return svc is not None
    except Exception:
        return False

class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    thread_id: str = ""

@app.get("/api/email/inbox")
async def email_inbox(limit: int = 10):
    loop = asyncio.get_event_loop()
    try:
        from core_os.skills.auto_lib import fetch_recent_emails
        emails = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: fetch_recent_emails(limit)),
            timeout=15
        )
        return {"ok": True, "emails": emails}
    except asyncio.TimeoutError:
        return {"ok": False, "error": "Gmail timeout — check OAuth token", "emails": []}
    except Exception as e:
        return {"ok": False, "error": str(e), "emails": []}

@app.post("/api/email/send")
async def email_send(req: SendEmailRequest):
    loop = asyncio.get_event_loop()
    try:
        from core_os.skills.auto_lib import send_email
        result = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: send_email(
                req.to, req.subject, req.body,
                thread_id=req.thread_id or None
            )),
            timeout=30
        )
        return result
    except asyncio.TimeoutError:
        return {"status": "error", "msg": "Send timeout"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

# ---------------------------------------------------------------------------
# NEURO STATE EDITOR
# ---------------------------------------------------------------------------
_NEURO_STATE_PATH = os.path.join(PROJECT_ROOT, "core_os", "memory", "neuro_state.json")

@app.get("/api/neuro")
async def neuro_get():
    try:
        if os.path.exists(_NEURO_STATE_PATH):
            with open(_NEURO_STATE_PATH) as f:
                return json.load(f)
        return {}
    except Exception as e:
        return {"error": str(e)}

@app.patch("/api/neuro")
async def neuro_patch(updates: dict):
    try:
        state = {}
        if os.path.exists(_NEURO_STATE_PATH):
            with open(_NEURO_STATE_PATH) as f:
                state = json.load(f)
        state.update({k: float(v) for k, v in updates.items() if isinstance(v, (int, float, str))})
        with open(_NEURO_STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
        return {"ok": True, "state": state}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ---------------------------------------------------------------------------
# VISION / IMAGE ANALYSIS
# ---------------------------------------------------------------------------
@app.post("/api/vision/analyze")
async def vision_analyze(image: UploadFile = File(...), prompt: str = "Describe what you see in detail."):
    import shutil
    suffix = ".jpg"
    if image.filename and "." in image.filename:
        suffix = "." + image.filename.rsplit(".", 1)[1].lower()
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        shutil.copyfileobj(image.file, tmp)
        tmp.close()
        loop = asyncio.get_event_loop()
        from core_os.skills.milla_vision import analyze_visuals
        description = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: analyze_visuals(tmp.name, prompt)),
            timeout=60
        )
        return {"ok": True, "description": description}
    except asyncio.TimeoutError:
        return {"ok": False, "description": "Vision timed out — moondream model may be loading"}
    except Exception as e:
        return {"ok": False, "description": f"Vision error: {e}"}
    finally:
        try: os.unlink(tmp.name)
        except Exception: pass

# ---------------------------------------------------------------------------
# SYSTEM UPDATER
# ---------------------------------------------------------------------------
# VISION SCREEN CHAT — browser sends base64 frame + message, Milla responds
# ---------------------------------------------------------------------------

class ScreenChatRequest(BaseModel):
    image: str        # base64-encoded PNG/JPEG
    message: str = "What do you see on my screen?"

@app.post("/api/vision/screen-chat")
async def vision_screen_chat(req: ScreenChatRequest):
    """
    Accepts a base64 screenshot from the browser + a user message.
    Runs moondream to describe the image, then passes the description
    + original message through Milla's chat pipeline for a full response.
    """
    import base64 as _b64
    if not req.image:
        return {"ok": False, "error": "No image provided"}

    # Decode base64 → temp file
    try:
        raw = req.image.split(",", 1)[-1]  # strip data:image/png;base64, prefix if present
        img_bytes = _b64.b64decode(raw)
    except Exception as e:
        return {"ok": False, "error": f"Image decode failed: {e}"}

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    try:
        tmp.write(img_bytes)
        tmp.close()

        loop = asyncio.get_event_loop()

        # Step 1: moondream describes the screen
        from core_os.skills.milla_vision import analyze_visuals
        vision_desc = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: analyze_visuals(tmp.name, req.message)),
            timeout=60
        )

        # Step 2: pass vision context through Milla's full chat pipeline
        augmented = (
            f"[SCREEN CAPTURE]\n{vision_desc}\n\n"
            f"[USER]: {req.message}"
        )
        history = load_shared_history(limit=10)
        messages = history + [{"role": "user", "content": augmented}]
        result = await loop.run_in_executor(None, lambda: model_manager.chat(messages=messages))
        reply = result.get("message", {}).get("content", vision_desc)

        # Persist to shared history
        append_shared_messages([
            {"role": "user",      "content": f"[Screen share] {req.message}"},
            {"role": "assistant", "content": reply},
        ])

        return {"ok": True, "vision": vision_desc, "response": reply}
    except asyncio.TimeoutError:
        return {"ok": False, "error": "Vision timed out — moondream loading"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        try: os.unlink(tmp.name)
        except Exception: pass

# ---------------------------------------------------------------------------
# SYSTEM UPDATER
# ---------------------------------------------------------------------------
@app.get("/api/system/updates")
async def system_updates():
    loop = asyncio.get_event_loop()
    def _check():
        result = sp.run(["checkupdates"], capture_output=True, text=True, timeout=30)
        lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
        return lines
    try:
        updates = await asyncio.wait_for(loop.run_in_executor(None, _check), timeout=35)
        return {"ok": True, "count": len(updates), "updates": updates}
    except Exception as e:
        return {"ok": False, "count": 0, "updates": [], "error": str(e)}

@app.get("/api/system/upgrade")
async def system_upgrade_stream():
    """SSE stream of live pacman upgrade output."""
    async def _stream():
        proc = await asyncio.create_subprocess_exec(
            "sudo", "pacman", "-Syu", "--noconfirm",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        try:
            async for line in proc.stdout:
                yield f"data: {line.decode(errors='replace').rstrip()}\n\n"
            await proc.wait()
            yield f"data: [EXIT:{proc.returncode}]\n\n"
        except Exception as e:
            yield f"data: [ERROR:{e}]\n\n"
    return StreamingResponse(_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

# ---------------------------------------------------------------------------
# DAILY BRIEF
# ---------------------------------------------------------------------------
_BRIEFS_DIR = os.path.join(PROJECT_ROOT, "core_os", "memory", "daily_briefs")

@app.get("/api/brief/latest")
async def brief_latest():
    if not os.path.exists(_BRIEFS_DIR):
        return {"ok": False, "brief": None}
    files = sorted([f for f in os.listdir(_BRIEFS_DIR) if f.endswith(".md")])
    if not files:
        return {"ok": False, "brief": None}
    latest = files[-1]
    try:
        with open(os.path.join(_BRIEFS_DIR, latest)) as f:
            content = f.read()
        return {"ok": True, "date": latest.replace("Summary_", "").replace(".md", ""), "content": content, "filename": latest}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/brief/list")
async def brief_list():
    if not os.path.exists(_BRIEFS_DIR):
        return {"ok": True, "briefs": []}
    files = sorted([f for f in os.listdir(_BRIEFS_DIR) if f.endswith(".md")], reverse=True)
    return {"ok": True, "briefs": [{"date": f.replace("Summary_","").replace(".md",""), "filename": f} for f in files]}

# ---------------------------------------------------------------------------
# DOCKER MANAGER
# ---------------------------------------------------------------------------
def _docker_cmd(*args, timeout=10):
    r = sp.run(["docker"] + list(args), capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

class DockerActionRequest(BaseModel):
    container: str

@app.get("/api/docker/list")
async def docker_list():
    loop = asyncio.get_event_loop()
    def _list():
        out, err, rc = _docker_cmd("ps", "-a", "--format",
            '{"id":"{{.ID}}","name":"{{.Names}}","image":"{{.Image}}","status":"{{.Status}}","state":"{{.State}}","ports":"{{.Ports}}"}')
        containers = []
        for line in out.splitlines():
            try: containers.append(json.loads(line))
            except Exception: pass
        return containers
    try:
        containers = await asyncio.wait_for(loop.run_in_executor(None, _list), timeout=12)
        return {"ok": True, "containers": containers}
    except Exception as e:
        return {"ok": False, "containers": [], "error": str(e)}

@app.post("/api/docker/start")
async def docker_start(req: DockerActionRequest):
    loop = asyncio.get_event_loop()
    _, err, rc = await loop.run_in_executor(None, lambda: _docker_cmd("start", req.container))
    return {"ok": rc == 0, "error": err}

@app.post("/api/docker/stop")
async def docker_stop(req: DockerActionRequest):
    loop = asyncio.get_event_loop()
    _, err, rc = await loop.run_in_executor(None, lambda: _docker_cmd("stop", req.container))
    return {"ok": rc == 0, "error": err}

@app.post("/api/docker/restart")
async def docker_restart(req: DockerActionRequest):
    loop = asyncio.get_event_loop()
    _, err, rc = await loop.run_in_executor(None, lambda: _docker_cmd("restart", req.container))
    return {"ok": rc == 0, "error": err}

@app.get("/api/docker/{container}/logs")
async def docker_logs(container: str, tail: int = 50):
    loop = asyncio.get_event_loop()
    out, err, rc = await loop.run_in_executor(None, lambda: _docker_cmd("logs", "--tail", str(tail), container, timeout=15))
    return {"ok": rc == 0, "logs": out or err}




# ═══════════════════════════════════════════════════════
# SYSTEM STATS
# ═══════════════════════════════════════════════════════
@app.get("/api/system/stats")
async def system_stats():
    loop = asyncio.get_event_loop()
    def _gather():
        cpu = psutil.cpu_percent(interval=0.4)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()
        uptime = int(_time.time() - psutil.boot_time())
        temps: dict = {}
        try:
            for k, entries in psutil.sensors_temperatures().items():
                if entries:
                    temps[k] = round(entries[0].current, 1)
        except Exception:
            pass
        procs = []
        try:
            for p in sorted(psutil.process_iter(['pid','name','cpu_percent','memory_percent']),
                            key=lambda x: x.info.get('cpu_percent') or 0, reverse=True)[:10]:
                procs.append({k: round(v, 1) if isinstance(v, float) else v
                              for k, v in p.info.items()})
        except Exception:
            pass
        return {
            "cpu_percent": cpu,
            "cpu_count": psutil.cpu_count(logical=True),
            "cpu_count_phys": psutil.cpu_count(logical=False),
            "mem_total_gb": round(mem.total / 1e9, 2),
            "mem_used_gb":  round(mem.used  / 1e9, 2),
            "mem_percent":  mem.percent,
            "disk_total_gb": round(disk.total / 1e9, 1),
            "disk_used_gb":  round(disk.used  / 1e9, 1),
            "disk_percent":  disk.percent,
            "net_sent_mb": round(net.bytes_sent / 1e6, 1),
            "net_recv_mb": round(net.bytes_recv / 1e6, 1),
            "uptime_secs": uptime,
            "temperatures": temps,
            "top_procs": procs,
        }
    try:
        data = await asyncio.wait_for(loop.run_in_executor(None, _gather), timeout=10)
        return {"ok": True, **data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════
# LOG VIEWER
# ═══════════════════════════════════════════════════════
_LOG_FILES = {
    "nexus-server": "/tmp/nexus-server.log",
    "milla-cron":   str(Path(PROJECT_ROOT) / "milla_cron.log"),
    "milla-auto":   "/tmp/milla-auto.log",
    "syslog":       "/var/log/syslog",
    "dreams":       str(Path(PROJECT_ROOT) / "core_os/memory/dreams.txt"),
}

@app.get("/api/logs/list")
async def logs_list():
    out = []
    for name, path in _LOG_FILES.items():
        try:
            size = os.path.getsize(path)
            out.append({"name": name, "path": path, "size_kb": round(size/1024,1), "exists": True})
        except Exception:
            out.append({"name": name, "path": path, "size_kb": 0, "exists": False})
    return {"ok": True, "logs": out}

@app.get("/api/logs/tail")
async def logs_tail(file: str = "nexus-server", lines: int = 200):
    path = _LOG_FILES.get(file)
    if not path:
        return {"ok": False, "error": "Unknown log name"}
    try:
        r = sp.run(["tail", f"-{lines}", path], capture_output=True, text=True, timeout=6)
        return {"ok": True, "content": r.stdout, "name": file}
    except Exception as e:
        return {"ok": False, "content": "", "error": str(e)}

@app.get("/api/logs/stream")
async def logs_stream(file: str = "nexus-server"):
    path = _LOG_FILES.get(file)
    async def _gen(p: str):
        if not p:
            yield "data: [unknown log]\n\n"
            return
        proc = await asyncio.create_subprocess_exec(
            "tail", "-f", "-n", "60", p,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            while True:
                try:
                    line = await asyncio.wait_for(proc.stdout.readline(), timeout=25)
                except asyncio.TimeoutError:
                    yield "data: [heartbeat]\n\n"
                    continue
                if not line:
                    break
                yield f"data: {line.decode(errors='replace').rstrip()}\n\n"
        finally:
            try: proc.kill()
            except Exception: pass
    return StreamingResponse(_gen(path or ""),
                             media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ═══════════════════════════════════════════════════════
# FILE BROWSER
# ═══════════════════════════════════════════════════════
_FILE_ROOT = Path(PROJECT_ROOT).resolve()
_SKIP_DIRS  = {"__pycache__", "node_modules", "hf_cache", "venv", ".git", "chroma_db"}
_BINARY_EXT = {".db", ".iso", ".png", ".jpg", ".jpeg", ".gif", ".pyc",
               ".whl", ".tar", ".gz", ".zip", ".wav", ".mp3", ".pkl", ".bin"}

def _safe(rel: str) -> Path:
    p = (_FILE_ROOT / rel).resolve()
    if not str(p).startswith(str(_FILE_ROOT)):
        raise HTTPException(400, "Path outside project root")
    return p

@app.get("/api/files/tree")
async def files_tree(path: str = ""):
    root = _safe(path)
    if not root.is_dir():
        return {"ok": False, "error": "Not a directory"}
    items = []
    try:
        for child in sorted(root.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
            if child.name.startswith('.') and child.name not in ('.env', '.env.example'):
                continue
            if child.name in _SKIP_DIRS:
                continue
            items.append({
                "name": child.name,
                "path": str(child.relative_to(_FILE_ROOT)),
                "type": "dir" if child.is_dir() else "file",
                "size": child.stat().st_size if child.is_file() else None,
                "ext": child.suffix.lower() if child.is_file() else None,
            })
    except PermissionError:
        pass
    return {"ok": True, "items": items, "cwd": str(root.relative_to(_FILE_ROOT)) or "."}

@app.get("/api/files/read")
async def files_read(path: str):
    p = _safe(path)
    if not p.is_file():
        return {"ok": False, "error": "Not a file"}
    if p.suffix.lower() in _BINARY_EXT:
        return {"ok": False, "error": "Binary file — cannot display as text"}
    try:
        content = p.read_text(errors='replace')
        return {"ok": True, "content": content, "path": str(p.relative_to(_FILE_ROOT))}
    except Exception as e:
        return {"ok": False, "error": str(e)}

class FileWriteReq(BaseModel):
    path: str
    content: str

@app.post("/api/files/write")
async def files_write(req: FileWriteReq):
    p = _safe(req.path)
    if p.suffix.lower() in _BINARY_EXT:
        return {"ok": False, "error": "Cannot overwrite binary file"}
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(req.content)
        return {"ok": True, "path": str(p.relative_to(_FILE_ROOT))}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════
# GIT PANEL
# ═══════════════════════════════════════════════════════
_GIT_ROOT = Path(PROJECT_ROOT)

def _git(*args, timeout=30):
    r = sp.run(["git", *args], capture_output=True, text=True, timeout=timeout, cwd=_GIT_ROOT)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

@app.get("/api/git/status")
async def git_status():
    loop = asyncio.get_event_loop()
    status, serr, src = await loop.run_in_executor(None, lambda: _git("status", "--short"))
    branch, _, _ = await loop.run_in_executor(None, lambda: _git("rev-parse", "--abbrev-ref", "HEAD"))
    remote, _, _ = await loop.run_in_executor(None, lambda: _git("remote", "get-url", "origin"))
    return {"ok": src == 0, "status": status, "branch": branch, "remote": remote, "error": serr}

@app.get("/api/git/log")
async def git_log(n: int = 25):
    loop = asyncio.get_event_loop()
    out, err, rc = await loop.run_in_executor(None,
        lambda: _git("log", f"-{n}", "--pretty=format:%h|%s|%an|%ar"))
    commits = []
    for line in out.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({"hash": parts[0], "subject": parts[1], "author": parts[2], "ago": parts[3]})
    return {"ok": rc == 0, "commits": commits}

@app.post("/api/git/pull")
async def git_pull():
    loop = asyncio.get_event_loop()
    out, err, rc = await asyncio.wait_for(
        loop.run_in_executor(None, lambda: _git("pull", "--ff-only", timeout=60)), timeout=65)
    return {"ok": rc == 0, "output": out or err}

class GitCommitReq(BaseModel):
    message: str

@app.post("/api/git/commit")
async def git_commit(req: GitCommitReq):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: _git("add", "-A"))
    out, err, rc = await loop.run_in_executor(None, lambda: _git("commit", "-m", req.message))
    return {"ok": rc == 0, "output": out or err}


# ═══════════════════════════════════════════════════════
# BACKUP MANAGER
# ═══════════════════════════════════════════════════════
_BACKUP_DIR = Path("/home/nexus/milla_backups")

@app.get("/api/backup/list")
async def backup_list():
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backups = []
    for f in sorted(_BACKUP_DIR.glob("*.tar.gz"), reverse=True)[:20]:
        stat = f.stat()
        backups.append({"name": f.name, "size_mb": round(stat.st_size/1e6, 1),
                        "created": round(stat.st_mtime)})
    return {"ok": True, "backups": backups}

@app.post("/api/backup/create")
async def backup_create():
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    from datetime import datetime
    name = f"nexus_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
    dest = _BACKUP_DIR / name
    sources = [s for s in [
        "core_os/memory/milla_long_term.db",
        "core_os/memory/neuro_state.json",
        "core_os/memory/persona_override.txt",
        ".env",
    ] if (_GIT_ROOT / s).exists()]
    loop = asyncio.get_event_loop()
    def _tar():
        cmd = ["tar", "-czf", str(dest), "-C", str(_GIT_ROOT)] + sources
        r = sp.run(cmd, capture_output=True, text=True, timeout=60)
        return r.returncode, r.stderr
    try:
        rc, err = await asyncio.wait_for(loop.run_in_executor(None, _tar), timeout=70)
        if rc != 0:
            return {"ok": False, "error": err}
        return {"ok": True, "name": name, "size_mb": round(dest.stat().st_size/1e6, 2)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════
# NOTIFICATIONS
# ═══════════════════════════════════════════════════════
@app.get("/api/notifications")
async def notifications():
    alerts: list[dict] = []
    loop = asyncio.get_event_loop()
    def _collect():
        local: list[dict] = []
        # Cron errors
        cron_log = _GIT_ROOT / "milla_cron.log"
        if cron_log.exists():
            try:
                tail = sp.run(["tail", "-80", str(cron_log)], capture_output=True, text=True, timeout=5).stdout
                n = tail.lower().count("error") + tail.lower().count("traceback")
                if n:
                    local.append({"type": "warn", "source": "cron", "text": f"{n} error(s) in recent cron log"})
            except Exception:
                pass
        # Server log
        srv = Path("/tmp/nexus-server.log")
        if srv.exists():
            try:
                tail = sp.run(["tail", "-30", str(srv)], capture_output=True, text=True, timeout=5).stdout
                if "error" in tail.lower() or "exception" in tail.lower():
                    local.append({"type": "warn", "source": "server", "text": "Recent errors in nexus-server.log"})
            except Exception:
                pass
        # Pending updates (skip if slow)
        try:
            r = sp.run(["checkupdates"], capture_output=True, text=True, timeout=15)
            n = len([l for l in r.stdout.strip().splitlines() if l.strip()])
            if n:
                local.append({"type": "info", "source": "updates", "text": f"{n} system updates available"})
        except Exception:
            pass
        return local
    try:
        alerts = await asyncio.wait_for(loop.run_in_executor(None, _collect), timeout=20)
    except Exception:
        pass
    return {"ok": True, "alerts": alerts, "count": len(alerts)}


# ═══════════════════════════════════════════════════════
# GLOBAL SEARCH
# ═══════════════════════════════════════════════════════
@app.get("/api/search")
async def global_search(q: str = "", limit: int = 30):
    if not q or len(q.strip()) < 2:
        return {"ok": True, "results": [], "query": q}
    results: list[dict] = []
    # Memory FTS5
    try:
        import sqlite3
        db_path = _GIT_ROOT / "core_os/memory/milla_long_term.db"
        if db_path.exists():
            con = sqlite3.connect(str(db_path))
            rows = con.execute(
                "SELECT rowid, fact, category FROM memories WHERE memories MATCH ? LIMIT 15",
                (q,)
            ).fetchall()
            con.close()
            for row in rows:
                results.append({"source": "memory", "id": row[0],
                                 "text": row[1][:200], "meta": row[2] or ""})
    except Exception:
        pass
    # Skill names/descriptions
    try:
        skills_dir = _GIT_ROOT / "core_os/skills"
        ql = q.lower()
        for py in skills_dir.glob("*.py"):
            if ql in py.stem.lower():
                results.append({"source": "skill", "id": py.stem,
                                 "text": py.name, "meta": "skill"})
    except Exception:
        pass
    # Agent feed files (search content)
    feed_files = [
        _GIT_ROOT / "core_os/memory/dreams.txt",
        _GIT_ROOT / "core_os/memory/stream_of_consciousness.md",
    ]
    for ff in feed_files:
        try:
            if ff.exists():
                lines = ff.read_text(errors="replace").splitlines()
                for i, line in enumerate(lines):
                    if q.lower() in line.lower() and line.strip():
                        results.append({"source": "feed", "id": f"{ff.name}:{i}",
                                         "text": line[:200], "meta": ff.name})
                        if len(results) >= limit:
                            break
        except Exception:
            pass
    return {"ok": True, "results": results[:limit], "query": q}


# ═══════════════════════════════════════════════════════
# CRON JOB CREATOR
# ═══════════════════════════════════════════════════════
class CronCreateReq(BaseModel):
    schedule: str   # e.g. "0 6 * * *"
    command: str    # shell command to run
    label: str = ""

@app.post("/api/cron/create")
async def cron_create(req: CronCreateReq):
    # Validate cron schedule (5 fields)
    parts = req.schedule.strip().split()
    if len(parts) != 5:
        return {"ok": False, "error": "Schedule must be 5 fields (min hr dom mon dow)"}
    cmd = req.command.strip()
    if not cmd:
        return {"ok": False, "error": "Command is required"}
    comment = f"# {req.label}" if req.label else ""
    new_line = f"{req.schedule} {cmd}"
    try:
        # Read current crontab
        r = sp.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        current = r.stdout if r.returncode == 0 else ""
        updated = current.rstrip("\n") + ("\n" + comment if comment else "") + "\n" + new_line + "\n"
        # Write back
        proc = sp.run(["crontab", "-"], input=updated, capture_output=True, text=True, timeout=5)
        if proc.returncode != 0:
            return {"ok": False, "error": proc.stderr}
        return {"ok": True, "line": new_line}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.delete("/api/cron/delete")
async def cron_delete(line: str):
    try:
        r = sp.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            return {"ok": False, "error": "Could not read crontab"}
        lines = [l for l in r.stdout.splitlines() if l.strip() != line.strip()]
        updated = "\n".join(lines) + "\n"
        proc = sp.run(["crontab", "-"], input=updated, capture_output=True, text=True, timeout=5)
        return {"ok": proc.returncode == 0, "error": proc.stderr}
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
