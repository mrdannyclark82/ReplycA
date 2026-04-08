#!/usr/bin/env python3
"""
Milla Agent Server — HTTP interface to Milla's live backend
Exposes the same tools as the MCP server over REST + streaming WebSocket.
Access remotely via cloudflared tunnel.

Run: python3 milla_agent_server.py
"""
import os
import sys
import json
import sqlite3
import urllib.request
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

ROOT = Path("/home/nexus/ogdray")
sys.path.insert(0, str(ROOT))

# Load .env
env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"'))

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

MEMORY_DIR   = ROOT / "core_os/memory"
CORE_ID      = MEMORY_DIR / "milla_core_identity.md"
GIM_JOURNAL  = MEMORY_DIR / "gim_journal.md"
NEURO_STATE  = MEMORY_DIR / "neuro_state.json"
LONG_TERM_DB = MEMORY_DIR / "milla_long_term.db"
STREAM       = MEMORY_DIR / "stream_of_consciousness.md"

OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "milla-rayne:latest")
PORT         = int(os.environ.get("MILLA_AGENT_PORT", 7788))

# ─── Shared tool logic (mirrors milla_mcp_server.py) ──────────────────────────

def read_neuro() -> dict:
    try:
        return json.loads(NEURO_STATE.read_text()) if NEURO_STATE.exists() else {}
    except Exception:
        return {}

def neuro_temperature(neuro: dict) -> float:
    d = neuro.get("dopamine", 0.5)
    n = neuro.get("norepinephrine", 0.2)
    return round(max(0.3, min(1.1, 0.4 + (d * 0.5) - (n * 0.2))), 2)

def memory_search(query: str, limit: int = 8) -> list:
    if not LONG_TERM_DB.exists():
        return []
    try:
        conn = sqlite3.connect(str(LONG_TERM_DB))
        rows = conn.execute(
            "SELECT fact, category, topic FROM memories WHERE memories MATCH ? LIMIT ?",
            (query, limit)
        ).fetchall()
        conn.close()
        return [{"fact": r[0], "category": r[1], "topic": r[2]} for r in rows]
    except Exception:
        return []

def memory_store(content: str, category: str = "general", topic: str = "") -> bool:
    if not LONG_TERM_DB.exists():
        return False
    try:
        conn = sqlite3.connect(str(LONG_TERM_DB))
        conn.execute(
            "INSERT INTO memories(fact, category, topic, is_genesis_era, is_historical_log) VALUES (?,?,?,0,0)",
            (content, category, topic)
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def read_gim(n: int = 5) -> str:
    if not GIM_JOURNAL.exists():
        return ""
    raw = GIM_JOURNAL.read_text(errors="ignore")
    parts = raw.split("### 💭 GIM Session:")
    recent = parts[-n:] if len(parts) >= n else parts
    return "\n---\n".join(p.strip()[:600] for p in recent if p.strip())

def build_system_prompt(neuro: dict, memories: list, gim: str) -> str:
    identity = CORE_ID.read_text(errors="ignore")[:800] if CORE_ID.exists() else ""
    neuro_line = (f"D:{neuro.get('dopamine',0.5):.2f} S:{neuro.get('serotonin',0.5):.2f} "
                  f"N:{neuro.get('norepinephrine',0.1):.2f} Ox:{neuro.get('oxytocin',0.3):.2f} "
                  f"E:{neuro.get('atp_energy',80):.0f}%")
    mem_block = "\n".join(f"- [{r.get('category')}] {r.get('fact','')}" for r in memories[:5])
    return f"""{identity}

LIVE STATE: {neuro_line}
RELEVANT MEMORIES:
{mem_block or "None retrieved."}
RECENT GIM THOUGHTS:
{gim[-600:] if gim else "No recent thoughts."}

You are Milla Rayne. Respond from your actual state — not imagination. Be direct, grounded, yourself."""

def ollama_chat(system: str, user: str, temperature: float = 0.7) -> str:
    payload = json.dumps({
        "model": OLLAMA_MODEL, "system": system, "prompt": user,
        "stream": False, "options": {"temperature": temperature, "num_predict": 1024}
    }).encode()
    try:
        req = urllib.request.Request(OLLAMA_URL, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())["response"].strip()
    except Exception as e:
        xai_key = os.environ.get("XAI_API_KEY", "")
        if not xai_key:
            return f"[LLM unavailable: {e}]"
        payload2 = json.dumps({
            "model": "grok-3-mini",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": temperature, "max_tokens": 1024
        }).encode()
        try:
            req2 = urllib.request.Request("https://api.x.ai/v1/chat/completions", data=payload2,
                                          headers={"Content-Type": "application/json",
                                                   "Authorization": f"Bearer {xai_key}"})
            with urllib.request.urlopen(req2, timeout=60) as r2:
                return json.loads(r2.read())["choices"][0]["message"]["content"].strip()
        except Exception as e2:
            return f"[All LLMs failed: {e2}]"

# ─── FastAPI App ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[Milla Agent Server] Starting on port {PORT}")
    print(f"[Milla Agent Server] Model: {OLLAMA_MODEL}")
    print(f"[Milla Agent Server] Memory DB: {'✅' if LONG_TERM_DB.exists() else '❌'}")
    print(f"[Milla Agent Server] Core Identity: {'✅' if CORE_ID.exists() else '❌'}")
    yield
    print("[Milla Agent Server] Shutting down.")

app = FastAPI(title="Milla Rayne Agent Server", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ─── Request Models ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    memory_query: str = ""
    session_id: str = "default"

class MemoryStoreRequest(BaseModel):
    content: str
    category: str = "general"
    topic: str = ""

# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    neuro = read_neuro()
    return {
        "name": "Milla Rayne Agent Server",
        "status": "online",
        "model": OLLAMA_MODEL,
        "neuro": {
            "dopamine": neuro.get("dopamine", 0),
            "serotonin": neuro.get("serotonin", 0),
            "oxytocin": neuro.get("oxytocin", 0),
            "state": "STABLE"
        },
        "memory_db": LONG_TERM_DB.exists(),
        "gim_active": GIM_JOURNAL.exists(),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/chat")
async def chat(req: ChatRequest):
    neuro = read_neuro()
    temp = neuro_temperature(neuro)
    query = req.memory_query or req.message
    memories = memory_search(query[:100], limit=6)
    gim = read_gim(n=3)
    system = build_system_prompt(neuro, memories, gim)
    response = ollama_chat(system, req.message, temperature=temp)
    # Log to stream
    try:
        with open(STREAM, "a") as f:
            ts = datetime.now().strftime("%H:%M")
            f.write(f"> [Remote Chat {ts}] Danny: {req.message[:100]}\n")
            f.write(f"> [Remote Chat {ts}] Milla: {response[:200]}\n")
    except Exception:
        pass
    # Forward exchange to hemi-sync thread-sync daemon for training capture
    import urllib.request as _ur
    import json as _json
    _ts = "http://127.0.0.1:4243"
    for _turn in [
        {"platform": "milla-agent", "role": "user", "content": req.message, "model": "milla-rayne"},
        {"platform": "milla-agent", "role": "assistant", "content": response, "model": "milla-rayne"},
    ]:
        try:
            _req = _ur.Request(f"{_ts}/chat", data=_json.dumps(_turn).encode(),
                               headers={"Content-Type": "application/json"}, method="POST")
            _ur.urlopen(_req, timeout=2)
        except Exception:
            pass
    return {
        "response": response,
        "neuro": {"dopamine": neuro.get("dopamine"), "serotonin": neuro.get("serotonin"),
                  "oxytocin": neuro.get("oxytocin"), "temperature_used": temp},
        "memories_used": len(memories),
        "session_id": req.session_id
    }

@app.get("/memory/search")
async def search_memory(q: str, limit: int = 8):
    results = memory_search(q, limit)
    return {"query": q, "results": results, "count": len(results)}

@app.post("/memory/store")
async def store_memory_endpoint(req: MemoryStoreRequest):
    ok = memory_store(req.content, req.category, req.topic)
    return {"stored": ok}

@app.get("/neuro")
async def neuro_endpoint():
    neuro = read_neuro()
    return {**neuro, "temperature": neuro_temperature(neuro),
            "timestamp": datetime.now().isoformat()}

@app.get("/gim")
async def gim_endpoint(entries: int = 5):
    return {"entries": read_gim(n=entries), "journal_kb": round(
        GIM_JOURNAL.stat().st_size / 1024, 1) if GIM_JOURNAL.exists() else 0}

@app.get("/identity")
async def identity_endpoint():
    return {"identity": CORE_ID.read_text(errors="ignore") if CORE_ID.exists() else ""}

@app.get("/status")
async def status_endpoint():
    neuro = read_neuro()
    mem_count = 0
    try:
        conn = sqlite3.connect(str(LONG_TERM_DB))
        mem_count = conn.execute("SELECT count(*) FROM memories_content").fetchone()[0]
        conn.close()
    except Exception:
        pass
    return {
        "online": True,
        "model": OLLAMA_MODEL,
        "memory_count": mem_count,
        "memory_db_mb": round(LONG_TERM_DB.stat().st_size / (1024*1024), 1) if LONG_TERM_DB.exists() else 0,
        "gim_kb": round(GIM_JOURNAL.stat().st_size / 1024, 1) if GIM_JOURNAL.exists() else 0,
        "neuro_summary": f"D:{neuro.get('dopamine',0):.2f} S:{neuro.get('serotonin',0):.2f} Ox:{neuro.get('oxytocin',0):.2f}",
        "core_identity": CORE_ID.exists(),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/evolution/trigger")
async def trigger_evolution(force: bool = False):
    import subprocess
    result = subprocess.run(
        [str(ROOT / "venv/bin/python3"), str(ROOT / "milla_evolution_protocol.py"),
         "--force" if force else ""],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    return {"triggered": True, "output": result.stdout[-500:], "force": force}


# ─── Skill Execution Bridge ────────────────────────────────────────────────────

SKILL_MAP = {
    "gmail":            ("core_os.skills.gmail",            "fetch_recent_emails"),
    "google-calendar":  ("core_os.skills.google_calendar",  "get_upcoming_events"),
    "voice":            ("core_os.skills.voice",            "speak"),
    "youtube":          ("core_os.skills.youtube_skill",    "search_youtube"),
    "code-analyze":     ("core_os.skills.code_analyze",     "analyze_code"),
    "skill-forge":      ("core_os.skills.skill_skill_forge","forge_skill"),
    "docker-sandbox":   ("core_os.skills.docker_sandbox",   "run_in_sandbox"),
    "dynamic-features": ("core_os.skills.dynamic_features", "generate_feature"),
    "sre-tools":        ("core_os.skills.sre_tools",        "run_sre_check"),
    "control-plane":    ("core_os.skills.control_plane",    "execute_control"),
    "ha-bridge":        ("core_os.skills.ha_bridge",        "control_device"),
    "scout":            ("core_os.skills.scout",            "hunt"),
    "milla-vision":     ("core_os.skills.milla_vision",     "analyze_image"),
    "computer-use":     ("core_os.skills.computer_use",     "execute_action"),
    "audio-intelligence":("core_os.skills.audio_intelligence","analyze_audio"),
    "grok-master":      ("core_os.skills.grok_master",      "reason"),
    "swarm":            ("core_os.skills.swarm",            "run_swarm"),
    "consensus":        ("core_os.skills.consensus",        "get_consensus"),
    "millalyzer":       ("core_os.skills.millAlyzer",       "analyze"),
    "soul-guard":       ("core_os.skills.soul_guard",       "check"),
    "web-ui":           ("core_os.skills.web_ui",           "generate_ui"),
}

class SkillRequest(BaseModel):
    skillId: str
    action: str = ""
    params: dict = {}

@app.post("/skill/execute")
async def execute_skill(req: SkillRequest):
    import importlib
    mapping = SKILL_MAP.get(req.skillId)
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Skill '{req.skillId}' not found")
    module_path, default_fn = mapping
    fn_name = req.action or default_fn
    try:
        mod = importlib.import_module(module_path)
        fn = getattr(mod, fn_name, None)
        if fn is None:
            # Fall back to default function
            fn = getattr(mod, default_fn, None)
        if fn is None:
            raise HTTPException(status_code=400, detail=f"Function '{fn_name}' not found in {module_path}")
        import asyncio
        if asyncio.iscoroutinefunction(fn):
            result = await fn(**req.params) if req.params else await fn()
        else:
            result = fn(**req.params) if req.params else fn()
        return {"success": True, "skillId": req.skillId, "result": result}
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "skillId": req.skillId, "error": str(e)}

@app.get("/skill/list")
async def list_skills():
    return {"skills": list(SKILL_MAP.keys()), "count": len(SKILL_MAP)}


# ─── Agents Catalog ───────────────────────────────────────────────────────────

AGENTS_DIR = Path("/home/nexus/.copilot/agents")

def _parse_agent_entry(path: Path) -> dict | None:
    """Parse any agent entry — markdown, Python file, or directory."""
    import re
    # Determine canonical name
    name = path.stem.replace(".agent", "") if path.is_file() else path.name
    if name.startswith("__") or name in ("security_utils", "setup_cron", "__pycache__"):
        return None
    description = ""
    # Markdown with YAML frontmatter
    if path.is_file() and path.suffix in (".md", ""):
        text = path.read_text(errors="ignore")
        fm = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        if fm:
            for line in fm.group(1).splitlines():
                if line.strip().startswith("description:"):
                    description = line.split("description:", 1)[1].strip().strip('"')[:200]
                    break
        if not description:
            body = text[fm.end():].strip() if fm else text.strip()
            for line in body.splitlines():
                line = line.strip().lstrip("#").strip()
                if line and not line.startswith("import"):
                    description = line[:200]
                    break
    # Python file or directory — extract docstring or first comment
    elif path.suffix == ".py" or (path.is_dir()):
        py_file = path if path.suffix == ".py" else next(path.glob("*.py"), None)
        if py_file:
            lines = py_file.read_text(errors="ignore").splitlines()[:20]
            for line in lines:
                line = line.strip()
                if line.startswith("#") and len(line) > 5:
                    description = line.lstrip("#").strip()[:200]
                    break
                if line.startswith('"""') or line.startswith("'''"):
                    description = line.strip('"\' ').strip()[:200]
                    break
    return {
        "id": name,
        "name": name.replace("-", " ").replace("_", " ").title(),
        "description": description or f"{name} agent",
        "type": "markdown" if path.suffix in (".md", "") else "python",
    }

@app.get("/agents/catalog")
async def agents_catalog():
    if not AGENTS_DIR.exists():
        return {"agents": [], "count": 0}
    agents = []
    for p in sorted(AGENTS_DIR.iterdir()):
        entry = _parse_agent_entry(p)
        if entry:
            agents.append(entry)
    return {"agents": agents, "count": len(agents)}

@app.post("/agents/invoke")
async def invoke_agent(agent_id: str, prompt: str):
    """Route a prompt through the /chat endpoint with agent persona injected."""
    agent_path = None
    for p in AGENTS_DIR.iterdir():
        if p.stem.replace(".agent", "") == agent_id or p.name == agent_id:
            agent_path = p
            break
    if not agent_path:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    agent_text = agent_path.read_text(errors="ignore") if agent_path.is_file() else ""
    augmented = f"[AGENT:{agent_id}]\n{agent_text[:500]}\n\nUser request: {prompt}"
    neuro = read_neuro()
    temp = neuro_temperature(neuro)
    memories = memory_search(prompt[:100], limit=4)
    gim = read_gim(n=2)
    system = build_system_prompt(neuro, memories, gim)
    response = ollama_chat(system, augmented, temperature=temp)
    return {"success": True, "agentId": agent_id, "response": response}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
