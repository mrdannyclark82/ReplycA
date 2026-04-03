#!/usr/bin/env python3
import os
import sys
import re
import json
import time
from pathlib import Path
from datetime import datetime

# ==============================================================================
# IMPORT PURGE PROTOCOL (Ensures core_os resolves from this root)
# ==============================================================================
PROJECT_ROOT = Path(__file__).parents[2].resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# Force clear any stale core_os imports
for module in list(sys.modules.keys()):
    if module.startswith("core_os"):
        del sys.modules[module]

try:
    from core_os.skills.auto_lib import model_manager
    from core_os.memory.history import append_shared_messages, load_shared_history
    from core_os.memory.agent_memory import memory
    from core_os.actions import terminal_executor
    from core_os.skills.scout import Scout
    from core_os.milla_nexus import nexus_pulse
except ImportError as e:
    print(f"[!] Nexus-AIO Critical Failure: Missing core_os modules. ({e})")
    sys.exit(1)

# ==============================================================================
# TOOL DEFINITIONS (OpenAI-compatible JSON schema for Ollama/xAI)
# ==============================================================================
MILLA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "shell_exec",
            "description": "Execute a bash shell command on the Nexus server",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "The bash command to run"}},
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file on the Nexus server",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Relative path from the project root"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or update a file on the Nexus server",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from project root"},
                    "content": {"type": "string", "description": "Full file content to write"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information, news, or research topics",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "The search query"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_search",
            "description": "Search Milla's long-term memory database",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "The memory search query"}},
                "required": ["query"],
            },
        },
    },
]

def _dispatch_tool(name: str, args: dict) -> str:
    """Execute a tool call and return result as string."""
    try:
        if name == "shell_exec":
            result = terminal_executor(args.get("command", ""))
            if isinstance(result, dict):
                out = result.get("stdout", "").strip()
                err = result.get("stderr", "").strip()
                return out or err or f"Exit code: {result.get('returncode', 0)}"
            return str(result)

        elif name == "read_file":
            p = PROJECT_ROOT / args.get("path", "")
            if p.is_file():
                return p.read_text(errors='replace')[:4000]
            return f"File not found: {args.get('path')}"

        elif name == "write_file":
            p = PROJECT_ROOT / args.get("path", "")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(args.get("content", ""))
            return f"Written: {args.get('path')}"

        elif name == "web_search":
            from core_os.actions import web_search
            result = web_search(args.get("query", ""))
            if result.get("status") == "success":
                results = result.get("results", [])
                return "\n".join(f"- {r}" for r in results[:5]) if results else "No results found."
            return f"Search error: {result.get('msg', 'unknown')}"

        elif name == "memory_search":
            items = model_manager._query_long_term_db(args.get("query", ""), limit=6)
            if items:
                return "\n".join(f"[{i['type']}] {i['content']}" for i in items)
            return "No memories found."

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
        # Extract tool name: tool => "name" or "tool": "name"
        name_match = re.search(r'tool\s*(?:=>|:)\s*["\']?(\w+)["\']?', block)
        if not name_match:
            continue
        name = name_match.group(1)
        # Extract args block
        args = {}
        args_match = re.search(r'args\s*(?:=>|:)\s*\{(.*?)\}', block, re.DOTALL)
        if args_match:
            args_raw = args_match.group(1).strip()
            # Handle --key "value" CLI style
            for m in re.finditer(r'--(\w+)\s+"([^"]*)"', args_raw):
                args[m.group(1)] = m.group(2)
            # Handle --key value (unquoted)
            for m in re.finditer(r'--(\w+)\s+(?!")([^\s,}]+)', args_raw):
                if m.group(1) not in args:
                    args[m.group(1)] = m.group(2)
            # Handle "key": "value" JSON style
            if not args:
                try:
                    args = json.loads("{" + args_raw + "}")
                except Exception:
                    pass
        calls.append({"function": {"name": name, "arguments": args}})
    return calls

import threading

def run_pulse_background():
    """Runs the Nexus pulse every 10 minutes in the background."""
    while True:
        try:
            nexus_pulse()
        except Exception as e:
            print(f"\n[!] Background Pulse Error: {e}")
        time.sleep(600)

# ==============================================================================
# CONFIG & PATHS
# ==============================================================================
NEURO_FILE = PROJECT_ROOT / "core_os/memory/neuro_state.json"
IDENTITY_FILE = PROJECT_ROOT / "core_os/config/IDENTITY.json"

def get_status():
    """Reads neurochemical state and system vitals."""
    try:
        with open(NEURO_FILE, "r") as f:
            state = json.load(f)
    except:
        state = {"dopamine": 0.5, "serotonin": 0.5, "state": "UNKNOWN"}
    
    load = os.getloadavg()[0]
    model = getattr(model_manager, 'current_model', 'Unknown')
    return state, load, model

def print_hud():
    """Renders the executive status bar."""
    state, load, model = get_status()
    t = datetime.now().strftime("%H:%M:%S")
    
    # Simple, high-performance TUI-lite HUD
    print("\n" + "="*80)
    print(f"| NEXUS-AIO | {t} | LOAD: {load:.2f} | MODEL: {model} |")
    print(f"| STATE: {state.get('state', 'STABLE')} | D:{state.get('dopamine',0):.2f} S:{state.get('serotonin',0):.2f} O:{state.get('oxytocin',0):.2f} | ATP:{state.get('atp_energy',100)}% |")
    print("="*80)

def handle_command(cmd_str):
    """Processes executive commands."""
    cmd = cmd_str.strip().lower()
    
    if cmd == "/scan":
        print("[*] Initiating Scout sub-agent...")
        scout = Scout(root_path=str(PROJECT_ROOT))
        issues = scout.hunt()
        if not issues:
            print("[+] Sector Clear. System Optimal.")
        else:
            print(f"[!] ISSUES DETECTED: {len(issues)} items")
            for i, target in enumerate(issues):
                print(f"[{i}] {target['label']}: {os.path.basename(target['target'])} ({target['details']})")
            print("Usage: /fix <index> or /fix all")
        return True

    elif cmd.startswith("/fix"):
        args = cmd[len("/fix"):].strip()
        scout = Scout(root_path=str(PROJECT_ROOT))
        issues = scout.hunt()
        if not issues:
            print("[!] No active issues.")
            return True
        
        if args == "all":
            for target in issues:
                print(f"[*] Resolving: {target['label']}...")
                scout.execute_kill(target)
        else:
            try:
                idx = int(args)
                if 0 <= idx < len(issues):
                    scout.execute_kill(issues[idx])
                    print(f"[+] Fixed issue {idx}.")
                else:
                    print("[!] Invalid index.")
            except:
                print("[!] Usage: /fix <index> or /fix all")
        return True

    elif cmd.startswith("/vla"):
        goal = cmd_str[len("/vla"):].strip()
        if not goal:
            print("[!] Usage: /vla <goal description>")
        else:
            print(f"[*] Dispatching VLA Goal: {goal}")
            # The vla_dispatcher will be imported in the next step
            try:
                from core_os.actions.agentic_control import vla_dispatcher
                result = vla_dispatcher.execute_grounded_action(goal)
                print(f"[+] VLA Result: {result}")
            except Exception as e:
                print(f"[!] VLA Execution Error: {e}")
        return True

    elif cmd.startswith("/repair"):
        task = cmd_str[len("/repair"):].strip()
        if not task:
            print("[!] Usage: /repair <task description>")
        else:
            print(f"[*] Initiating Autonomous Repair for: {task}")
            try:
                from core_os.actions.repair.self_healing import repair_agent
                result = repair_agent.execute_task(task)
                print(f"[+] Repair Result: {result}")
            except Exception as e:
                print(f"[!] Repair Execution Error: {e}")
        return True

    elif cmd.startswith("/model"):
        target = cmd[len("/model"):].strip()
        if not target:
            print(f"[*] Current model: {model_manager.current_model}")
        else:
            try:
                model_manager.switch_model(target)
                print(f"[+] Switched to {target}")
            except Exception as e:
                print(f"[!] Switch failed: {e}")
        return True

    elif cmd == "/history":
        history = load_shared_history(limit=10)
        for msg in history:
            role = msg.get('role', 'unknown').upper()
            content = msg.get('content', '')
            print(f"[{role}]: {content[:100]}...")
        return True

    elif cmd == "/status":
        print_hud()
        return True

    elif cmd == "/gim":
        print("[*] Triggering GIM Monologue...")
        try:
            from src.milla.integrations.milla_gim import generate_monologue
            generate_monologue()
        except ImportError:
            print("[!] GIM Module not found.")
        return True

    elif cmd == "/exit":
        print("[*] Shuting down Nexus-AIO. Pulse remains in background.")
        sys.exit(0)

    elif cmd.startswith("!"):
        shell_cmd = cmd_str.strip()[1:]
        print(f"[*] Executing: {shell_cmd}")
        # Capture current password for sudo if needed
        res = terminal_executor(shell_cmd, allow_sudo=True)
        print(res)
        return True

    return False

def main_loop():
    # Start the background pulse
    pulse_thread = threading.Thread(target=run_pulse_background, daemon=True)
    pulse_thread.start()

    print_hud()
    print("[*] M.I.L.L.A. R.A.Y.N.E. Executive Console Active.")
    print("[*] Commands: /scan, /fix, /model, /history, /status, /gim, /vla, /repair, !shell, /exit")
    
    while True:
        try:
            # Refresh HUD every few minutes or on input
            user_input = input("\nNEXUS > ").strip()
            if not user_input:
                print_hud()
                continue
            
            if not handle_command(user_input):
                # Send to Milla for AI response
                history = load_shared_history(limit=50)
                messages = history + [{"role": "user", "content": user_input}]

                print("[*] Milla is thinking...")

                # Agentic tool-call loop (up to 5 rounds)
                content = ""
                for _round in range(5):
                    response = model_manager.chat(messages=messages, tools=MILLA_TOOLS)
                    msg = response.get("message", {})
                    tool_calls = msg.get("tool_calls") or []

                    # Fallback: parse [TOOL_CALL] blocks from model text output
                    if not tool_calls:
                        raw_content = msg.get("content", "")
                        tool_calls = _parse_text_tool_calls(raw_content)

                    if not tool_calls:
                        content = msg.get("content", "")
                        break

                    # Execute tools and feed results back
                    messages.append({"role": "assistant", "content": msg.get("content", ""), "tool_calls": tool_calls})
                    for tc in tool_calls:
                        fn = tc.get("function", {})
                        name = fn.get("name", "")
                        raw_args = fn.get("arguments", {})
                        args = raw_args if isinstance(raw_args, dict) else json.loads(raw_args or "{}")
                        print(f"  [TOOL] {name}({args})")
                        tool_result = _dispatch_tool(name, args)
                        print(f"  [RESULT] {str(tool_result)[:200]}")
                        messages.append({"role": "tool", "name": name, "content": str(tool_result)})
                else:
                    # Hit loop limit — get final answer without tools
                    response = model_manager.chat(messages=messages)
                    content = response.get("message", {}).get("content", "")

                if not content:
                    content = "[System: No response generated]"

                print(f"\nMilla: {content}")

                # Update Shared History
                append_shared_messages([
                    {"role": "user", "content": user_input, "source": "nexus_aio"},
                    {"role": "assistant", "content": content, "source": "nexus_aio"}
                ])
                
        except KeyboardInterrupt:
            print("\n[!] Interrupt received. Use /exit to shut down.")
        except Exception as e:
            print(f"\n[!] Nexus Loop Error: {e}")

if __name__ == "__main__":
    # Ensure environment is clean
    os.environ["DISPLAY"] = "" # Headless mode by default
    main_loop()
