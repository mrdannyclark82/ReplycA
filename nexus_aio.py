#!/usr/bin/env python3
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# ==============================================================================
# IMPORT PURGE PROTOCOL (Ensures core_os resolves from this root)
# ==============================================================================
PROJECT_ROOT = Path(__file__).parent.resolve()
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
except ImportError as e:
    print(f"[!] Nexus-AIO Critical Failure: Missing core_os modules. ({e})")
    sys.exit(1)

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
    print_hud()
    print("[*] M.I.L.L.A. R.A.Y.N.E. Executive Console Active.")
    print("[*] Commands: /scan, /fix, /model, /history, !shell, /exit")
    
    while True:
        try:
            # Refresh HUD every few minutes or on input
            user_input = input("\nNEXUS > ").strip()
            if not user_input:
                print_hud()
                continue
            
            if not handle_command(user_input):
                # Send to Milla for AI response
                messages = [{"role": "user", "content": user_input}]
                # Integrate history
                history = load_shared_history(limit=5)
                full_messages = history + messages
                
                print("[*] Milla is thinking...")
                response = model_manager.chat(messages=full_messages)
                content = response['message']['content']
                
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
