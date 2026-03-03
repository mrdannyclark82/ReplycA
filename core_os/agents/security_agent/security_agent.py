import os
import subprocess
import json
import sys
from datetime import datetime

# Import shared utils
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import security_utils

DATA_DIR = security_utils.DATA_DIR
STATE_FILE = os.path.join(DATA_DIR, "security_state.json")

def monitor_processes():
    flags = []
    # Use ps -aux for simple process listing
    try:
        proc = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        lines = proc.stdout.splitlines()
        
        # Simple heuristic: Look for known suspicious commands in arguments
        suspicious_cmds = ["nc -l", "wget -O", "curl | bash", "chmod +x /tmp", "rm -rf /", "sudo -S"]
        
        for line in lines[1:]:  # Skip header
            for cmd in suspicious_cmds:
                if cmd in line:
                    flags.append(f"Suspicious process found: {line.strip()}")
    except Exception as e:
        flags.append(f"Failed to check processes: {e}")
        
    return flags

def monitor_bash_history():
    flags = []
    history_file = os.path.expanduser("~/.bash_history")
    
    # Load last checked line count
    state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
        except: pass
        
    last_line = state.get("bash_history_line", 0)
    
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", errors="ignore") as f:
                lines = f.readlines()
                current_count = len(lines)
                
                # Check new lines
                new_lines = lines[last_line:] if current_count > last_line else lines
                
                suspicious_keywords = ["rm -rf", "sudo su", "chmod 777", "wget ", "curl ", "nc "]
                for line in new_lines:
                    for keyword in suspicious_keywords:
                        if keyword in line:
                            flags.append(f"Suspicious command in history: {line.strip()}")
                            
                # Update state
                state["bash_history_line"] = current_count
                with open(STATE_FILE, "w") as f:
                    json.dump(state, f)
        except Exception as e:
            flags.append(f"Failed to read bash history: {e}")
            
    return flags

def main():
    print("Running Security Agent...")
    os.makedirs(DATA_DIR, exist_ok=True)
    
    process_flags = monitor_processes()
    history_flags = monitor_bash_history()
    
    all_flags = process_flags + history_flags
    
    if all_flags:
        print(f"Found {len(all_flags)} flags. Triggering Investigative Agent.")
        for flag in all_flags:
            security_utils.log_flag("Security Agent", flag, level="high")
            
        # Trigger next agent: Investigative Agent
        next_agent = os.path.join(os.path.dirname(__file__), "../investigative_agent/investigative_agent.py")
        security_utils.trigger_next_agent(next_agent)
    else:
        print("No suspicious activity detected.")

if __name__ == "__main__":
    main()
