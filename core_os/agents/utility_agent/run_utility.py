#!/usr/bin/env python3
"""
General purpose helper (e.g., data‑wrangling, quick math, file ops).
"""

import sys
import os
import json
from datetime import datetime

# Add project root and agents folder to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
AGENTS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if AGENTS_ROOT not in sys.path:
    sys.path.append(AGENTS_ROOT)

import security_utils
from core_os.actions import terminal_executor
from core_os.skills.auto_lib import model_manager

DATA_DIR = security_utils.DATA_DIR

import re

def extract_content(text):
    """Extracts code or command from triple backticks."""
    pattern = r"```(?:python3|python|bash)?(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

def main():
    print("💡 utility_agent is up and running!")
    
    # Check for pending tasks
    task_file = os.path.join(DATA_DIR, "utility_tasks.json")
    if not os.path.exists(task_file):
        print(f"No pending utility tasks at {task_file}")
        return

    try:
        with open(task_file, "r") as f:
            tasks = json.load(f)
        
        new_tasks = [t for t in tasks if t.get("status") == "pending"]
        if not new_tasks:
            print("No new utility tasks.")
            return

        for task in new_tasks:
            print(f"[*] Processing Task: {task.get('description')}")
            
            # Step 1: Use model to generate the necessary command or python code
            prompt = f"""
            You are the Milla Utility Agent. 
            Task: {task.get('description')}
            Context: {task.get('context', 'None')}
            
            Provide the bash command or python code to execute this task inside triple backticks. 
            If you provide python code, start the block with 'python3:'.
            """
            
            response = model_manager.chat(messages=[{"role": "user", "content": prompt}])
            raw_content = response.get('message', {}).get('content', '').strip()
            command_or_code = extract_content(raw_content)
            
            if command_or_code:
                print(f"[*] Executing: {command_or_code[:100]}...")
                if command_or_code.startswith("python3:"):
                    # Execute python code
                    python_code = command_or_code.replace("python3:", "").strip()
                    tmp_file = os.path.join(DATA_DIR, f"tmp_util_{datetime.now().strftime('%H%M%S')}.py")
                    with open(tmp_file, "w") as f:
                        f.write(python_code)
                    res = terminal_executor(f"python3 {tmp_file}")
                    os.remove(tmp_file)
                else:
                    # Execute bash command
                    res = terminal_executor(command_or_code)
                
                if res['stderr']:
                    task["status"] = "failed"
                    task["error"] = res['stderr']
                else:
                    task["status"] = "completed"
                    task["output"] = res['stdout']
            else:
                task["status"] = "error"
                task["error"] = "No command or code generated."

        # Save updated tasks
        with open(task_file, "w") as f:
            json.dump(tasks, f, indent=4)

    except Exception as e:
        print(f"Error in utility_agent: {e}")

if __name__ == "__main__":
    main()
