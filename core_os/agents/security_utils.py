import json
import os
import subprocess
from datetime import datetime

DATA_DIR = os.path.expanduser("~/security_data")
FLAGS_FILE = os.path.join(DATA_DIR, "security_flags.json")

def log_flag(agent_name, details, level="medium"):
    """Logs a security flag to the shared file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    flag = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "details": details,
        "level": level,
        "status": "new"
    }

    flags = []
    if os.path.exists(FLAGS_FILE):
        try:
            with open(FLAGS_FILE, "r") as f:
                flags = json.load(f)
        except json.JSONDecodeError:
            pass

    flags.append(flag)
    
    with open(FLAGS_FILE, "w") as f:
        json.dump(flags, f, indent=4)
    
    return flag

def trigger_next_agent(agent_script_path, context=None):
    """Triggers the next agent in the chain."""
    print(f"Triggering next agent: {agent_script_path}")
    try:
        # Pass context as an argument or environment variable if needed
        # For simplicity, we just run the script, it will read the flags file
        subprocess.Popen(["python3", agent_script_path], start_new_session=True)
    except Exception as e:
        print(f"Failed to trigger next agent: {e}")
