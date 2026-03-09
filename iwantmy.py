import os
import json
import sqlite3
import subprocess
import pyautogui
import easyocr
import ollama
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed
from duckduckgo_search import DDGS

# Initialize Vision (OCR)
reader = easyocr.Reader(['en'], gpu=False)

# --- TOOLS ---

def screen_vision():
    """Reads the current terminal text via OCR."""
    path = f"core_os/screenshots/v_{datetime.now().strftime('%H%M%S')}.png"
    pyautogui.screenshot().save(path)
    results = reader.readtext(path, detail=0)
    return {"visible_text": "\n".join(results[-50:]), "path": path}

def terminal_executor(command: str):
    """Executes a command and returns the outcome."""
    try:
        res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        return {"stdout": res.stdout, "stderr": res.stderr, "success": res.returncode == 0}
    except Exception as e:
        return {"error": str(e)}

def web_search(query: str):
    """Finds fixes for errors online."""
    with DDGS() as ddgs:
        return {"results": [r for r in ddgs.text(query, max_results=3)]}

# --- THE SELF-REPAIR LOOP ---

class SelfHealingAgent:
    def __init__(self, model="qwen3-coder:480b-cloud"):
        self.model = model
        self.history = []
        self.tools = [terminal_executor, screen_vision, web_search]

    def run(self, task, max_retries=5):
        print(f"[*] Task Initiated: {task}")
        current_prompt = task
        
        for attempt in range(max_retries):
            print(f"\n[Iteration {attempt + 1}/{max_retries}] Thinking...")
            
            # 1. Ask Qwen for the next action
            response = ollama.chat(
                model=self.model,
                messages=self.history + [{'role': 'user', 'content': current_prompt}],
                tools=self.tools
            )
            
            msg = response['message']
            self.history.append({'role': 'user', 'content': current_prompt})
            self.history.append(msg)

            # 2. If the model wants to act
            if msg.get('tool_calls'):
                for tool in msg['tool_calls']:
                    name = tool['function']['name']
                    args = tool['function']['arguments']
                    
                    print(f" [Action] {name}({args})")
                    
                    # Tool Dispatcher
                    if name == "terminal_executor": result = terminal_executor(**args)
                    elif name == "screen_vision": result = screen_vision(**args)
                    elif name == "web_search": result = web_search(**args)
                    
                    self.history.append({'role': 'tool', 'content': json.dumps(result)})
                    
                    # 3. SELF-HEALING LOGIC: If a terminal command failed, 
                    # immediately trigger a "Vision Check" to see what happened.
                    if name == "terminal_executor" and not result.get("success"):
                        print(" [!] Command failed. Triggering Self-Repair Vision...")
                        vision_data = screen_vision()
                        current_prompt = f"The command failed. Screen says: {vision_data['visible_text']}. Find a fix and try again."
                        break # Go back to the model with the error + vision data
                else:
                    # If all tools in this turn succeeded, ask for a status update
                    current_prompt = "The previous action completed. Check the screen to verify if the task is done."
            else:
                # 4. Final Conclusion
                print("\n[Final Response]:", msg['content'])
                if "TASK COMPLETE" in msg['content'].upper():
                    break
                current_prompt = "Continue the task if not finished."

if __name__ == "__main__":
    agent = SelfHealingAgent()
    # "I Want It All" style prompt
    agent.run("Install the package 'numpy', but I think my pip is broken. Look at the screen for errors and fix whatever is wrong until numpy is working.")
