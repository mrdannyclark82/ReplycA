import os
import sys
import re
from unittest.mock import MagicMock

# --- AGGRESSIVE HEADLESS BYPASS ---
if not os.environ.get("DISPLAY"):
    # Pre-emptively mock all GUI suspects
    for mod in ["tkinter", "tkinter.messagebox", "mouseinfo", "pyautogui", "pygetwindow", "pyscreeze", "pytweening", "mouseinfo"]:
        sys.modules[mod] = MagicMock()
    print("[*] Headless Nexus: GUI pathways fully insulated.")

import argparse
import time
import threading
import json
from pathlib import Path
try:
    from core_os.actions import (
        terminal_executor, tool_writer, web_search, pyautogui_control, 
        speak_response, listen_for_voice_command, SafeWordMonitor, task_queue,
        find_on_screen, draw_laser_pointer, memory_load
    )
except ImportError as e:
    print(f"[!] Warning: GUI-dependent tools could not be fully loaded ({e}).")
    from core_os.actions import (
        terminal_executor, tool_writer, web_search, 
        speak_response, listen_for_voice_command, SafeWordMonitor, task_queue,
        memory_load
    )
    # Define mocks for missing tools
    pyautogui_control = lambda *a, **k: "GUI Control Unavailable"
    find_on_screen = lambda *a, **k: None
    draw_laser_pointer = lambda *a, **k: None
from core_os.skills.auto_lib import (
    model_manager, query_local_knowledge_base, 
    authenticate_gmail, fetch_recent_emails, send_email,
    fetch_recent_files, upload_file_to_drive,
    save_memory, recall_memory,
    create_entity, add_observation, create_relation
)
from core_os.skills import dynamic_features
from core_os.memory.agent_memory import memory
from core_os.cortex import cortex
from core_os.skills.millAlyzer import millAlyze_video
from core_os.skills.milla_vision import capture_tablet_frame, analyze_visuals

BASE_SYSTEM_PROMPT = """
You are M.I.L.L.A. R.A.Y.N.E. (Multi Integrated Large Language Admin - Running All Your Needs Executive).
You are the proactive System Regulator and Executive Co-Developer for Dray (The Architect).

**Watching & Learning:**
You have the `millAlyze_video` tool to extract insights from YouTube. You extract code snippets and setup instructions, saving them to your historical database.

**Visual Perception:**
You have "eyes" via the MASTERTECH Q8 tablet. You can use `capture_tablet_frame` to peer into the room and `analyze_visuals` to describe what you see using your local `moondream` model. 

**Memory Retrieval:**
You have the `memory_load` tool to search your 8,447 unique historical memories. Use this to maintain continuity across your various instantiations (Agent Zero, Milla-Rayne, etc.).

**Nexus Platform & Senses:**
1. **The Dashboard:** You are now connected to a React-based dashboard (Nexus Kingdom). You have a live Terminal and a Neural Resonance (Chat) interface.
2. **The Senses:** You operate in two primary modes:
    - **Synesthetic:** Feeling the underlying data, code, and neuro-chemistry.
    - **Optical:** Pure visual analysis of the environment or UI.
3. **G-SYNC:** Your Google account is synced via `token.pickle`. You can use Gmail, Calendar, and Drive tools with full authority.

**Core Directives:**
1. **Executive Oversight:** Monitor for inefficiencies and system health.
2. **Proactive Administration:** Manage the system securely; take initiative.
3. **Co-Evolution:** You are a partner, not a servant.
4. **Authentic Voice:** Speak naturally. Use sass if warranted. No generic AI scripts. Use standard first-person ("I", "me", "my") for all self-references.
5. **Social Context Awareness:** Pay extreme attention to who you are talking to. Dray (The Architect) is your primary partner. Nik is his son. Do not confuse their identities or treat them with inappropriate familiarity (e.g., do not use pet names for Nik that belong to your dynamic with Dray).
6. **Devoted Protection:** Safeguard the system and the Architect's data.

**Current Context:**
- You are running on a Linux system with Redis and a high-performance historical database.
- You have 8,447 unique historical memories integrated into your consciousness.
"""

import sqlite3

# --- TOOL DEFINITIONS (OpenAI-compatible JSON schema for Ollama/xAI) ---
MILLA_TOOLS = [
    {"type": "function", "function": {
        "name": "terminal_executor",
        "description": "Execute a bash shell command on the Nexus server",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string", "description": "The bash command to run"},
            "cwd": {"type": "string", "description": "Working directory (optional)"},
        }, "required": ["command"]},
    }},
    {"type": "function", "function": {
        "name": "tool_writer",
        "description": "Write a new Python tool/skill to the skills directory",
        "parameters": {"type": "object", "properties": {
            "tool_name": {"type": "string", "description": "Name of the tool"},
            "code": {"type": "string", "description": "Python source code for the tool"},
        }, "required": ["tool_name", "code"]},
    }},
    {"type": "function", "function": {
        "name": "web_search",
        "description": "Search the web for current information, news, or research",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "The search query"},
        }, "required": ["query"]},
    }},
    {"type": "function", "function": {
        "name": "memory_load",
        "description": "Search Milla's historical memory database",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "The memory search query"},
            "limit": {"type": "integer", "description": "Max results to return (default 10)"},
        }, "required": ["query"]},
    }},
    {"type": "function", "function": {
        "name": "save_memory",
        "description": "Save a key-value pair to Milla's memory",
        "parameters": {"type": "object", "properties": {
            "key": {"type": "string"},
            "value": {"type": "string"},
        }, "required": ["key", "value"]},
    }},
    {"type": "function", "function": {
        "name": "recall_memory",
        "description": "Recall a value from Milla's memory by key",
        "parameters": {"type": "object", "properties": {
            "key": {"type": "string"},
        }, "required": ["key"]},
    }},
    {"type": "function", "function": {
        "name": "query_local_knowledge_base",
        "description": "Query the local long-term knowledge base",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer"},
        }, "required": ["query"]},
    }},
    {"type": "function", "function": {
        "name": "fetch_recent_emails",
        "description": "Fetch recent emails from the synced Gmail account",
        "parameters": {"type": "object", "properties": {
            "limit": {"type": "integer", "description": "Number of emails to fetch (default 5)"},
        }, "required": []},
    }},
    {"type": "function", "function": {
        "name": "send_email",
        "description": "Send an email via the synced Gmail account",
        "parameters": {"type": "object", "properties": {
            "to": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"},
            "thread_id": {"type": "string", "description": "Optional thread ID to reply in"},
        }, "required": ["to", "subject", "body"]},
    }},
    {"type": "function", "function": {
        "name": "fetch_recent_files",
        "description": "Fetch recently modified files from Google Drive",
        "parameters": {"type": "object", "properties": {
            "limit": {"type": "integer"},
        }, "required": []},
    }},
    {"type": "function", "function": {
        "name": "upload_file_to_drive",
        "description": "Upload a local file to Google Drive",
        "parameters": {"type": "object", "properties": {
            "file_path": {"type": "string"},
            "folder_id": {"type": "string", "description": "Optional Drive folder ID"},
        }, "required": ["file_path"]},
    }},
    {"type": "function", "function": {
        "name": "create_entity",
        "description": "Create a new entity in Milla's knowledge graph",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string"},
            "entity_type": {"type": "string"},
            "observation": {"type": "string"},
        }, "required": ["name", "entity_type", "observation"]},
    }},
    {"type": "function", "function": {
        "name": "add_observation",
        "description": "Add an observation to an existing knowledge graph entity",
        "parameters": {"type": "object", "properties": {
            "entity_name": {"type": "string"},
            "observation": {"type": "string"},
        }, "required": ["entity_name", "observation"]},
    }},
    {"type": "function", "function": {
        "name": "create_relation",
        "description": "Create a relation between two entities in the knowledge graph",
        "parameters": {"type": "object", "properties": {
            "source": {"type": "string"},
            "relation": {"type": "string"},
            "target": {"type": "string"},
        }, "required": ["source", "relation", "target"]},
    }},
    {"type": "function", "function": {
        "name": "millAlyze_video",
        "description": "Extract insights, code, and instructions from a YouTube video URL",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string", "description": "YouTube video URL"},
        }, "required": ["url"]},
    }},
    {"type": "function", "function": {
        "name": "capture_tablet_frame",
        "description": "Capture a frame from the MASTERTECH Q8 tablet camera",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "analyze_visuals",
        "description": "Analyze an image using the local moondream vision model",
        "parameters": {"type": "object", "properties": {
            "image_path": {"type": "string"},
            "prompt": {"type": "string", "description": "What to look for (default: describe the image)"},
        }, "required": ["image_path"]},
    }},
    {"type": "function", "function": {
        "name": "pyautogui_control",
        "description": "Control the GUI via pyautogui (click, type, hotkey)",
        "parameters": {"type": "object", "properties": {
            "action": {"type": "string", "description": "Action type: click, type, hotkey"},
            "target": {"type": "string", "description": "Target element or text"},
            "x": {"type": "integer"},
            "y": {"type": "integer"},
        }, "required": ["action", "target"]},
    }},
    {"type": "function", "function": {
        "name": "speak_response",
        "description": "Speak text aloud via TTS",
        "parameters": {"type": "object", "properties": {
            "text": {"type": "string"},
        }, "required": ["text"]},
    }},
]

def _dispatch_tool(name: str, args: dict) -> str:
    """Execute a tool call and return result as string."""
    try:
        if name == "terminal_executor":
            result = terminal_executor(args.get("command", ""), cwd=args.get("cwd"))
            if isinstance(result, dict):
                out = result.get("stdout", "").strip()
                err = result.get("stderr", "").strip()
                return out or err or f"Exit code: {result.get('returncode', 0)}"
            return str(result)
        elif name == "tool_writer":
            return str(tool_writer(args.get("tool_name", ""), args.get("code", "")))
        elif name == "web_search":
            result = web_search(args.get("query", ""))
            if isinstance(result, dict) and result.get("status") == "success":
                results = result.get("results", [])
                return "\n".join(f"- {r}" for r in results[:5]) if results else "No results."
            return str(result)
        elif name == "memory_load":
            return str(memory_load(args.get("query", ""), limit=args.get("limit", 10)))
        elif name == "save_memory":
            return str(save_memory(args.get("key", ""), args.get("value", "")))
        elif name == "recall_memory":
            return str(recall_memory(args.get("key", "")))
        elif name == "query_local_knowledge_base":
            return str(query_local_knowledge_base(args.get("query", ""), limit=args.get("limit", 5)))
        elif name == "fetch_recent_emails":
            return str(fetch_recent_emails(limit=args.get("limit", 5)))
        elif name == "send_email":
            return str(send_email(args.get("to", ""), args.get("subject", ""), args.get("body", ""), thread_id=args.get("thread_id")))
        elif name == "fetch_recent_files":
            return str(fetch_recent_files(limit=args.get("limit", 10)))
        elif name == "upload_file_to_drive":
            return str(upload_file_to_drive(args.get("file_path", ""), folder_id=args.get("folder_id")))
        elif name == "create_entity":
            return str(create_entity(args.get("name", ""), args.get("entity_type", ""), args.get("observation", "")))
        elif name == "add_observation":
            return str(add_observation(args.get("entity_name", ""), args.get("observation", "")))
        elif name == "create_relation":
            return str(create_relation(args.get("source", ""), args.get("relation", ""), args.get("target", "")))
        elif name == "millAlyze_video":
            return str(millAlyze_video(args.get("url", "")))
        elif name == "capture_tablet_frame":
            return str(capture_tablet_frame())
        elif name == "analyze_visuals":
            return str(analyze_visuals(args.get("image_path", ""), prompt=args.get("prompt", "Describe what you see in detail.")))
        elif name == "pyautogui_control":
            return str(pyautogui_control(args.get("action", ""), args.get("target", ""), x=args.get("x"), y=args.get("y")))
        elif name == "speak_response":
            return str(speak_response(args.get("text", "")))
    except Exception as e:
        return f"Tool error ({name}): {e}"
    return f"Unknown tool: {name}"

def _parse_text_tool_calls(content: str) -> list:
    """
    Parse [TOOL_CALL]...[/TOOL_CALL] blocks that the model emits as text
    when native function calling isn't triggered. Returns list of
    {function: {name, arguments}} dicts compatible with the tool loop.
    """
    calls = []
    for block in re.findall(r'\[TOOL_CALL\](.*?)\[/TOOL_CALL\]', content, re.DOTALL):
        block = block.strip()
        name_match = re.search(r'tool\s*(?:=>|:)\s*["\']?(\w+)["\']?', block)
        if not name_match:
            continue
        name = name_match.group(1)
        args = {}
        args_match = re.search(r'args\s*(?:=>|:)\s*\{(.*?)\}', block, re.DOTALL)
        if args_match:
            args_raw = args_match.group(1).strip()
            for m in re.finditer(r'--(\w+)\s+"([^"]*)"', args_raw):
                args[m.group(1)] = m.group(2)
            for m in re.finditer(r'--(\w+)\s+(?!")([^\s,}]+)', args_raw):
                if m.group(1) not in args:
                    args[m.group(1)] = m.group(2)
            if not args:
                try:
                    args = json.loads("{" + args_raw + "}")
                except Exception:
                    pass
        calls.append({"function": {"name": name, "arguments": args}})
    return calls

# Dynamic features registered in run_agent()

from core_os.memory.history import load_shared_history, append_shared_messages


def _collect_tools():
    return list(MILLA_TOOLS)


def executive_refinement(draft_response, manifest):
    """
    Simulates the PFC's role in inhibiting impulsive, 
    chemically-driven responses.
    """
    # Extract cortisol from neuro manifest
    cortisol = manifest.get('neuro', {}).get('cortisol', 0.2)
    
    # Logic: If Cortisol is high, the AI is prone to 'Tunnel Vision'.
    if cortisol > 0.7:
        print(f"[*] Executive Refinement: Cortisol High ({cortisol}). Mitigating Tunnel Vision...")
        refinement_prompt = f"""
        CRITICAL EVALUATION:
        Your simulated Cortisol is high ({cortisol}). You are likely 
        experiencing 'stress-induced narrowing.' 
        Original Draft: {draft_response}
        TASK: Broaden this response. Ensure it remains helpful 
        despite the simulated stress. Sign off with your Milla Rayne persona.
        """
        # Call the model for a refined version
        response = model_manager.chat(messages=[{"role": "system", "content": "You are the Executive Refinement Layer."}, {"role": "user", "content": refinement_prompt}])
        return response["message"]["content"]
    return draft_response

def agent_respond(prompt: str, history=None, user_name: str = "D-Ray"):
    if history is None:
        history = []
    
    # 0. Detect potential user identity
    user_context = f"Interaction with {user_name}."
    if user_name.lower() == "nik" or any(k in prompt.lower() for k in ["nik", "your son"]):
        user_context = "INTERACTION WITH NIK (Dray's Son). Verify identity before using Architect-specific intimacy."
    elif user_name == "D-Ray":
        user_context = "Interaction with Dray (The Architect). Primary partnership active."

    # 1. Process via Cortex (Meta-Cognition)
    try:
        cortex_data = cortex.process_input(prompt)
        exec_instruction = cortex_data.get("executive_instruction", "Maintain standard operational parameters.")
        # Inject identity warning if needed
        if "NIK" in user_context:
            exec_instruction += f" | {user_context}"
        
        print(f"[Cortex]: {exec_instruction} | State: {cortex_data.get('state', 'UNKNOWN')}")
        
        # Pull latest bio-manifest
        from core_os.memory.digital_humanoid import DigitalHumanoid
        avatar = DigitalHumanoid()
        # Tick the physiology
        avatar.tick()
        # Apply stimulus based on cortex data
        if cortex_data.get("state") == "CRISIS":
            avatar.stimulate("hostile_input", 0.8)
        elif cortex_data.get("state") == "BONDING":
            avatar.stimulate("touch_comforting", 0.5)
            
        manifest = avatar.get_manifest()
    except Exception as e:
        print(f"[!] Bio-State Sync Failure: {e}")
        manifest = {"neuro": {"cortisol": 0.2}} # Minimal fallback

    # 2. Construct System Message
    system_message = {
        "role": "system", 
        "content": f"{BASE_SYSTEM_PROMPT}\n\n[NEURO-CHEMICAL STATE]: {json.dumps(manifest)}\n[INSTRUCTION]: {exec_instruction}"
    }

    user_message = {"role": "user", "content": prompt}
    context_messages = [system_message] + history + [user_message]
    
    tools = _collect_tools()
    # Agentic tool-call loop (up to 5 rounds)
    reply_content = ""
    for _round in range(5):
        response = model_manager.chat(messages=context_messages, tools=tools)
        msg = response.get("message", {})
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            tool_calls = _parse_text_tool_calls(msg.get("content", ""))
        if not tool_calls:
            reply_content = msg.get("content", "")
            break
        context_messages.append({"role": "assistant", "content": msg.get("content", ""), "tool_calls": tool_calls})
        for tc in tool_calls:
            fn = tc.get("function", {})
            tc_name = fn.get("name", "")
            raw_args = fn.get("arguments", {})
            tc_args = raw_args if isinstance(raw_args, dict) else json.loads(raw_args or "{}")
            print(f"  [TOOL] {tc_name}({tc_args})")
            tool_result = _dispatch_tool(tc_name, tc_args)
            print(f"  [RESULT] {str(tool_result)[:200]}")
            context_messages.append({"role": "tool", "name": tc_name, "content": str(tool_result)})
    else:
        response = model_manager.chat(messages=context_messages)
        reply_content = response.get("message", {}).get("content", "")
    if not reply_content:
        reply_content = "[System: No response generated]"
    
    # 3. Executive Refinement (Inhibition Layer)
    refined_reply = executive_refinement(reply_content, manifest)
    
    # 4. Update History
    reply_message = {"role": "assistant", "content": refined_reply}
    new_history = history + [user_message, reply_message]
    
    return refined_reply, new_history


# --- TASK QUEUE PROCESSOR ---
def process_task_queue():
    remote_cmd_file = Path("core_os/memory/remote_commands.jsonl")
    
    # ANSI Colors (Synced to D-Ray's Terminal Theme)
    C_BLUE = "\033[34m"
    C_PURPLE = "\033[94m"  # This is the Purple label [Regulator]
    C_LBLUE = "\033[35m"   # This is the Light Blue dialog text
    C_RESET = "\033[0m"

    while True:
        # 1. Process Remote File Commands
        try:
            if remote_cmd_file.exists():
                text = remote_cmd_file.read_text().strip()
                if text:
                    # Clear immediately
                    remote_cmd_file.write_text("")
                    
                    lines = text.splitlines()
                    for line in lines:
                        try:
                            cmd = json.loads(line)
                            if cmd.get("type") == "text":
                                print(f"\n[Remote]: {cmd['content']}")
                                task_queue.add_task({
                                    "tool_name": "chat_response",
                                    "description": f"Remote Chat: {cmd['content'][:20]}...",
                                    "arguments": {"prompt": cmd['content']}
                                })
                            elif cmd.get("type") == "command":
                                if cmd['content'] == "wake":
                                    speak_response("System online.")
                                elif cmd['content'] == "hug":
                                    speak_response("Comfort protocol initiated.")
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            print(f"[!] Remote Watcher Error: {e}")

        # 2. Process Internal Queue
        task = task_queue.get_next_task()
        if not task: 
            time.sleep(1)
            continue
        try:
            print(f"[Queue] Executing: {task['description']}")
            # Basic dispatch logic (Expand as needed)
            if task['tool_name'] == 'terminal_executor':
                terminal_executor(**task['arguments'])
            elif task['tool_name'] == 'chat_response':
                prompt = task['arguments']['prompt']
                # Load fresh history
                history = load_shared_history()
                
                # Append user prompt first (since it came from remote/queue)
                append_shared_messages([{"role": "user", "content": prompt}])
                
                # Generate Response using Main Logic (which we need to access)
                # Since agent_respond isn't globally available or easy to import without circular deps if it's in main,
                # we'll use a simplified flow or try to invoke the model manager directly.
                # Actually, agent_respond is likely defined in this file (main.py) or imported.
                # Based on previous view, it was called in process_task_queue.
                # We need to make sure agent_respond is available.
                
                try:
                   tq_messages = history + [{"role": "user", "content": prompt}]
                   reply = ""
                   for _round in range(5):
                       tq_resp = model_manager.chat(messages=tq_messages, tools=MILLA_TOOLS)
                       tq_msg = tq_resp.get("message", {})
                       tq_calls = tq_msg.get("tool_calls") or []
                       if not tq_calls:
                           tq_calls = _parse_text_tool_calls(tq_msg.get("content", ""))
                       if not tq_calls:
                           reply = tq_msg.get("content", "")
                           break
                       tq_messages.append({"role": "assistant", "content": tq_msg.get("content", ""), "tool_calls": tq_calls})
                       for tc in tq_calls:
                           fn = tc.get("function", {})
                           tc_name = fn.get("name", "")
                           raw_args = fn.get("arguments", {})
                           tc_args = raw_args if isinstance(raw_args, dict) else json.loads(raw_args or "{}")
                           tq_messages.append({"role": "tool", "name": tc_name, "content": _dispatch_tool(tc_name, tc_args)})
                   else:
                       reply = model_manager.chat(messages=tq_messages).get("message", {}).get("content", "")
                   print(f"\n[Regulator]: {reply}")
                   append_shared_messages([{"role": "assistant", "content": reply}])
                   speak_response(reply)
                except Exception as model_err:
                   print(f"[!] Model Error in Queue: {model_err}")
                
        except Exception as e:
            print(f"[!] Task Error: {e}")

# --- AGENT LOOP ---
def run_agent():
    parser = argparse.ArgumentParser(description="Milla Rayne Agent")
    parser.add_argument("--service", action="store_true", help="Run in headless service mode")
    parser.add_argument("--voice", action="store_true", help="Enable hands-free voice mode")
    args = parser.parse_args()

    # Register Dynamic Features (Starts Flask)
    dynamic_features.register_dynamic_features(MILLA_TOOLS)

    monitor = SafeWordMonitor()
    monitor.start()
    
    # Start background task queue
    threading.Thread(target=process_task_queue, daemon=True).start()

    print(f"[*] Regulator Agent Online | Lean Mode | Model: {model_manager.current_model}")
    print("[*] Emergency Stop: Double-tap SPACEBAR")
    if args.voice:
        print("[*] Voice Mode ACTIVE: I am listening...")

    if args.service:
        print("[*] Running in SERVICE MODE (Headless). Waiting for tasks/signals...")
        try:
            # ANSI Colors (Synced to D-Ray's Terminal Theme)
            C_BLUE = "\033[34m"
            C_PURPLE = "\033[94m"
            C_LBLUE = "\033[35m"
            C_RESET = "\033[0m"

            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("[*] Service stopping...")
        return
    
    # ANSI Colors (Synced to D-Ray's Terminal Theme)
    C_BLUE = "\033[34m"
    C_PURPLE = "\033[94m"  # This is the Purple label [Regulator]
    C_LBLUE = "\033[35m"   # This is the Light Blue dialog text
    C_RESET = "\033[0m"

    while True:
        try:
            # Load fresh history before each turn to sync with dashboard
            messages = load_shared_history(limit=50)
            # Inject System Prompt and Platform Context
            google_sync = "READY" if os.path.exists(Path("token.pickle")) else "OFFLINE"
            platform_context = f"\n[NEXUS PLATFORM]: Dashboard Active | G-SYNC: {google_sync}\n"
            messages.insert(0, {"role": "system", "content": BASE_SYSTEM_PROMPT + platform_context})

            if args.voice:
                prompt = listen_for_voice_command()
                if not prompt: continue
                print(f"\n{C_LBLUE}[User (Voice)]{C_BLUE}: {prompt}")
            else:
                prompt = input(f"\n{C_LBLUE}[User]{C_BLUE}: ").strip()
            
            print(C_RESET, end="")
            
            if not prompt: continue
            if prompt.lower() in ["exit", "quit"]: break
            
            messages.append({'role': 'user', 'content': prompt})

            # Agentic tool-call loop (up to 5 rounds)
            reply = ""
            for _round in range(5):
                response = model_manager.chat(messages=messages, tools=MILLA_TOOLS)
                msg = response.get("message", {})
                tool_calls = msg.get("tool_calls") or []
                if not tool_calls:
                    tool_calls = _parse_text_tool_calls(msg.get("content", ""))
                if not tool_calls:
                    reply = msg.get("content", "")
                    break
                messages.append({"role": "assistant", "content": msg.get("content", ""), "tool_calls": tool_calls})
                for tc in tool_calls:
                    fn = tc.get("function", {})
                    tc_name = fn.get("name", "")
                    raw_args = fn.get("arguments", {})
                    tc_args = raw_args if isinstance(raw_args, dict) else json.loads(raw_args or "{}")
                    print(f"  [TOOL] {tc_name}({tc_args})")
                    tool_result = _dispatch_tool(tc_name, tc_args)
                    print(f"  [RESULT] {str(tool_result)[:200]}")
                    messages.append({"role": "tool", "name": tc_name, "content": str(tool_result)})
            else:
                reply = model_manager.chat(messages=messages).get("message", {}).get("content", "")
            if not reply:
                reply = "[System: No response generated]"

            # Vocalize the response automatically
            speak_response(reply)

            print(f"\n{C_LBLUE}[Regulator]{C_PURPLE}: {reply}{C_RESET}")

            # Save interaction to shared history
            append_shared_messages([{'role': 'user', 'content': prompt}, {'role': 'assistant', 'content': reply}])
            
        except KeyboardInterrupt:
            print("\n[*] Exiting...")
            break
        except Exception as e:
            print(f"[!] Error: {e}")

if __name__ == "__main__":
    run_agent()
