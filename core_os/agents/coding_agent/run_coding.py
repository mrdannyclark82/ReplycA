#!/usr/bin/env python3
"""
Handles code generation, linting and formatting tasks.
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
from core_os.actions import terminal_executor, tool_writer
from core_os.skills.auto_lib import model_manager

DATA_DIR = security_utils.DATA_DIR

import re

def extract_code(text):
    """Extracts Python code from triple backticks or returns the whole text if none found."""
    # Look for ```python or ``` code blocks
    pattern = r"```(?:python)?(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

def main():
    print("💡 coding_agent is up and running!")
    
    # Check for pending tasks
    task_file = os.path.join(DATA_DIR, "coding_tasks.json")
    if not os.path.exists(task_file):
        print(f"No pending coding tasks at {task_file}")
        return

    try:
        with open(task_file, "r") as f:
            tasks = json.load(f)
        
        new_tasks = [t for t in tasks if t.get("status") == "pending"]
        if not new_tasks:
            print("No new coding tasks.")
            return

        for task in new_tasks:
            print(f"[*] Processing Task: {task.get('description')}")
            
            prompt = f"""
            You are the Milla Coding Agent. 
            Task: {task.get('description')}
            Context: {task.get('context', 'None')}
            
            Provide ONLY the Python code for this task inside triple backticks. 
            """
            
            response = model_manager.chat(messages=[{"role": "user", "content": prompt}])
            raw_content = response.get('message', {}).get('content', '')
            code = extract_code(raw_content)
            
            if code:
                print(f"[*] Extracted Code:\n{code}\n")
                # Save the code
                tool_name = task.get('tool_name', f"task_{datetime.now().strftime('%H%M%S')}")
                res = tool_writer(tool_name, code)
                
                if res.get('status') == 'error':
                    task["status"] = "failed"
                    task["error"] = res.get('msg', 'Unknown error in tool_writer')
                    print(f"[!] Tool Writer Error: {res.get('msg')}")
                    continue

                # Test the code (Syntax check)
                test_res = terminal_executor(f"python3 -m py_compile core_os/dynamic_tools/{tool_name}.py")
                if test_res['stderr']:
                    task["status"] = "failed"
                    task["error"] = test_res['stderr']
                else:
                    task["status"] = "completed"
                    task["output_file"] = f"core_os/dynamic_tools/{tool_name}.py"
            else:
                task["status"] = "error"
                task["error"] = "No code generated."

        # Save updated tasks
        with open(task_file, "w") as f:
            json.dump(tasks, f, indent=4)

    except Exception as e:
        print(f"Error in coding_agent: {e}")

if __name__ == "__main__":
    main()
