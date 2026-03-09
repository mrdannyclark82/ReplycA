import tk
import os
import time
import json
import sqlite3
import subprocess
import threading
import asyncio
import tk
import pyautogui
import easyocr
import importlib.util
from datetime import datetime
from bs4 import BeautifulSoup
from pynput import keyboard
from playsound3 import playsound
from duckduckgo_search import DDGS
import ollama

# --- GLOBAL CONFIG & STATE ---
STOP_FLAG = False
reader = easyocr.Reader(['en'], gpu=False) 
DYNAMIC_TOOLS_PATH = "core_os/dynamic_tools"
os.makedirs(DYNAMIC_TOOLS_PATH, exist_ok=True)

# --- LAYER A: THE EMERGENCY BRAKE ---
class SafeWordMonitor(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.last_space = 0
        
    def on_press(self, key):
        global STOP_FLAG
        if key == keyboard.Key.space:
            now = time.time()
            if now - self.last_space < 0.3:
                STOP_FLAG = True
                print("\n[!!!] REGULATORS, STAND DOWN: SAFE WORD DETECTED")
                return False 
            self.last_space = now

    def run(self):
        with keyboard.Listener(on_press=self.on_press) as listener:
            listener.join()

# --- LAYER: MEMORY & SELF-IMPROVEMENT ---
class AgentMemory:
    def __init__(self, db_path="core_os/memory/agent_memory.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS mem (k TEXT PRIMARY KEY, v TEXT, t DATETIME)')
        self.conn.commit()

    def remember(self, key, value):
        self.cursor.execute("INSERT OR REPLACE INTO mem VALUES (?, ?, ?)", (key, value, datetime.now()))
        self.conn.commit()
        return f"Memory Locked: {key}"

    def recall(self, key):
        self.cursor.execute("SELECT v FROM mem WHERE k=?", (key,))
        res = self.cursor.fetchone()
        return res[0] if res else "None."

# --- LAYER: TOOL CREATION (The Self-Evolution Engine) ---
def tool_writer(tool_name: str, code: str):
    """
    Core Capability: Allows the agent to write and deploy its own Python tools.
    The agent can literally upgrade its own skill set mid-session.
    """
    file_path = os.path.join(DYNAMIC_TOOLS_PATH, f"{tool_name}.py")
    try:
        with open(file_path, "w") as f:
            f.write(code)
        # Fix permissions for Arch (rwxr-xr-x)
        os.chmod(file_path, 0o755)
        return {"status": "success", "msg": f"New skill '{tool_name}' forged at {file_path}"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

def list_dynamic_tools():
    """Checks the workshop for any custom forged tools."""
    return [f.replace(".py", "") for f in os.listdir(DYNAMIC_TOOLS_PATH) if f.endswith(".py")]

# --- LAYER: UI & SPATIAL AWARENESS ---
def draw_laser_pointer(x, y, w, h, duration=2000):
    def create_box():
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True, "-alpha", 0.5)
        root.geometry(f"{w+20}x{h+10}+{x-10}+{y-5}")
        canvas = tk.Canvas(root, bg="cyan", highlightthickness=0) # Cyan for 'Writing' mode
        canvas.pack(fill="both", expand=True)
        root.after(duration, root.destroy)
        root.mainloop()
    threading.Thread(target=create_box, daemon=True).start()

def find_on_screen(target_text):
    shot_path = "core_os/screenshots/scan.png"
    os.makedirs(os.path.dirname(shot_path), exist_ok=True)
    pyautogui.screenshot().save(shot_path)
    results = reader.readtext(shot_path)
    for (bbox, text, prob) in results:
        if str(target_text).lower() in text.lower():
            x_min, y_min = int(bbox[0][0]), int(bbox[0][1])
            return x_min, y_min, int(bbox[1][0] - x_min), int(bbox[2][1] - y_min)
    return None

# --- LAYER: SYSTEM EXECUTION ---
def terminal_executor(command: str):
    global STOP_FLAG
    if STOP_FLAG: return "Aborted."
    # Basic safety filter (Expand this as needed)
    if "rm -rf /" in command: return "Blocked: I ain't bricking your Arch install, homie."
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
    return {"stdout": result.stdout, "stderr": result.stderr}

# --- THE ORCHESTRATOR ---
memory = AgentMemory()

def run_agent(prompt):
    global STOP_FLAG
    model_name = os.getenv("OLLAMA_MODEL", "kimi-k2.5:cloud")
    monitor = SafeWordMonitor()
    monitor.start()

    # Base tools + Discovery of any forged tools
    tools = [terminal_executor, tool_writer, memory.remember, memory.recall]
    
    print(f"[*] Regulator Agent Online | Model: {model_name}")
    print(f"[*] Task: {prompt}")

    # Step 1: Reasoning / Planning
    response = ollama.chat(
        model=model_name, 
        messages=[{'role': 'user', 'content': prompt}], 
        tools=tools
    )
    
    # Show the "Think" block if Qwen3 is ruminating
    if hasattr(response.message, 'thinking'):
        print(f"\n[Thinking]:\n{response.message.thinking}\n")

    messages = [{'role': 'user', 'content': prompt}, response['message']]

    # Step 2: Tool Execution Loop
    if response['message'].get('tool_calls'):
        for tool_call in response['message']['tool_calls']:
            if STOP_FLAG: break
            name = tool_call['function']['name']
            args = tool_call['function']['arguments']

            # Highlighting logic for terminal interaction
            if name == "terminal_executor":
                coords = find_on_screen("main.py") or find_on_screen("nano")
                if coords: draw_laser_pointer(*coords)

            print(f" [Exec] Running {name}...")
            func_map = {
                "terminal_executor": terminal_executor, 
                "tool_writer": tool_writer, 
                "remember": memory.remember, 
                "recall": memory.recall
            }
            
            result = func_map[name](**args)
            messages.append({'role': 'tool', 'content': json.dumps(result), 'name': name})

        # Final Synthesis
        final = ollama.chat(model=model_name, messages=messages)
        print("\n[Regulator]:", final['message']['content'])
    else:
        print("\n[Regulator]:", response['message']['content'])

if __name__ == "__main__":
    # Test: Force the agent to realize it needs a new tool, write it, and use it.
    run_agent("You need a way to check CPU temperature on Arch. If you don't have a tool for it, write one using 'tool_writer', then execute it.")
