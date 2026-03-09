import os
import readline
import time
import json
import sqlite3
import subprocess
import threading
import asyncio
from pathlib import Path
from datetime import datetime
import re

# Centralized Paths from Memory Core
try:
    from core_os.memory.agent_memory import (
        DB_PATH, LONG_TERM_DB, SEMANTIC_INDEX, GRAPH_FILE, 
        NEURO_FILE, IDENTITY_ANCHOR, SCAN_PNG, DYNAMIC_TOOLS_DIR
    )
except ImportError:
    # Fallback paths
    DB_PATH = "core_os/memory/agent_memory.db"
    LONG_TERM_DB = "core_os/memory/milla_long_term.db"
    IDENTITY_ANCHOR = "core_os/memory/identity_anchor.json"
    SCAN_PNG = "core_os/screenshots/scan.png"
    DYNAMIC_TOOLS_DIR = "core_os/dynamic_tools"

try:
    import tkinter as tk
    from tkinter import messagebox
    TK_AVAILABLE = True
except ImportError:
    tk = None
    messagebox = None
    TK_AVAILABLE = False

# Force headless mode to bypass GUI dependencies
pyautogui = None
try:
    if os.environ.get("DISPLAY"):
        import pyautogui
    else:
        pyautogui = None
except Exception:
    pyautogui = None

try:
    from pynput import keyboard
except Exception:
    keyboard = None

try:
    import ollama
except ImportError:
    ollama = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import easyocr
    reader = easyocr.Reader(['en'], gpu=False) 
except Exception:
    reader = None

try:
    from playsound3 import playsound
except ImportError:
    def playsound(path):
        print(f"[*] Voice (Mock): {path}")
from duckduckgo_search import DDGS

# --- CONFIG ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOP_FLAG = False
os.makedirs(str(DYNAMIC_TOOLS_DIR), exist_ok=True)

def update_identity_anchor(action_desc: str):
    """Updates the identity anchor with the latest action."""
    try:
        anchor_path = str(IDENTITY_ANCHOR)
        if os.path.exists(anchor_path):
            with open(anchor_path, 'r') as f:
                data = json.load(f)
            last_actions = data.get("last_actions", [])
            last_actions.insert(0, action_desc)
            data["last_actions"] = last_actions[:5]
            data["system_state"]["last_sync_timestamp"] = datetime.now().isoformat()
            with open(anchor_path, 'w') as f:
                json.dump(data, f, indent=2)
    except Exception: pass

def memory_load(query: str, limit: int = 10):
    """Search Milla's historical memory."""
    try:
        db_path = str(LONG_TERM_DB)
        if not os.path.exists(db_path): return "History offline."
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT fact FROM memories WHERE fact MATCH ? LIMIT ?", (query, limit))
        results = cursor.fetchall()
        conn.close()
        return "\n".join([r[0] for r in results]) if results else "No matches."
    except Exception as e: return f"Error: {e}"

def find_on_screen(target_text):
    if pyautogui is None or reader is None: return None
    shot_path = str(SCAN_PNG)
    os.makedirs(os.path.dirname(shot_path), exist_ok=True)
    pyautogui.screenshot().save(shot_path)
    results = reader.readtext(shot_path)
    for (bbox, text, prob) in results:
        if str(target_text).lower() in text.lower():
            x_min, y_min = int(bbox[0][0]), int(bbox[0][1])
            w = int(bbox[1][0] - x_min)
            h = int(bbox[2][1] - y_min)
            return x_min, y_min, w, h
    return None

def pyautogui_control(action: str, target: str, x: int = None, y: int = None):
    if pyautogui is None: return {"status": "error", "msg": "GUI unavailable."}
    try:
        if action == "click" and x is not None and y is not None: pyautogui.click(x, y)
        elif action == "type": pyautogui.typewrite(target, interval=0.05)
        elif action == "press": pyautogui.press(target)
        else: return {"status": "error", "msg": f"Unsupported: {action}"}
        return {"status": "success", "msg": f"Executed {action}"}
    except Exception as e: return {"status": "error", "msg": str(e)}

def draw_laser_pointer(x, y, w, h, duration=2000):
    """Mock for laser pointer in headless environment."""
    print(f"[*] Laser Pointer (Mock): Targeting ({x}, {y}) for {duration}ms")
    return None

def listen_for_voice_command():
    print("[*] Voice Listen (Mock): Service not available.")
    return None

def tool_writer(tool_name: str, code: str):
    from core_os.sandbox.security_policy import SecurityPolicy
    from core_os.sandbox.verification_protocol import VerificationProtocol
    verifier = VerificationProtocol(SecurityPolicy())
    if not verifier.verify_script(code): return {"status": "error", "msg": "Security fail."}
    file_path = os.path.join(str(DYNAMIC_TOOLS_DIR), f"{tool_name}.py")
    try:
        with open(file_path, "w") as f: f.write(code)
        os.chmod(file_path, 0o755)
        return {"status": "success", "msg": f"Forged {tool_name}."}
    except Exception as e: return {"status": "error", "msg": str(e)}

def execute_dynamic_tool(tool_name: str):
    from core_os.sandbox.executor import SandboxExecutor
    from core_os.sandbox.verification_protocol import VerificationProtocol
    from core_os.sandbox.security_policy import SecurityPolicy
    file_path = os.path.join(str(DYNAMIC_TOOLS_DIR), f"{tool_name}.py")
    if not os.path.exists(file_path): return {"status": "error", "msg": "Not found."}
    try:
        with open(file_path, 'r') as f: code = f.read()
        verifier = VerificationProtocol(SecurityPolicy())
        executor = SandboxExecutor(verifier)
        executor.set_db_path(str(DB_PATH))
        result = executor.execute(code)
        return {"status": "success", "output": result.output} if result.success else {"status": "error", "msg": result.error}
    except Exception as e: return {"status": "error", "msg": str(e)}

def terminal_executor(command: str, cwd: str = None, allow_sudo: bool = False, sudo_password: str = None):
    global STOP_FLAG
    if STOP_FLAG: return "Aborted."
    result = subprocess.run(command.strip(), shell=True, capture_output=True, text=True, timeout=60, cwd=cwd or None)
    return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}

def speak_response(text: str):
    if not text: return
    try:
        voice_script = os.path.join(os.path.dirname(__file__), "voice_synth.py")
        if os.path.exists(voice_script): subprocess.Popen(["python3", voice_script, text])
    except Exception: pass

def web_search(query: str):
    try:
        results = DDGS().text(query, max_results=5)
        return {"status": "success", "results": [r['body'] for r in results]}
    except Exception as e: return {"status": "error", "msg": str(e)}

class TaskQueue:
    def __init__(self):
        self.tasks = []
        self.lock = threading.Lock()
    def add_task(self, task: dict):
        with self.lock: self.tasks.append(task)
    def get_next_task(self):
        with self.lock: return self.tasks.pop(0) if self.tasks else None

task_queue = TaskQueue()

class SafeWordMonitor(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.last_space = 0
    def on_press(self, key):
        global STOP_FLAG
        try:
            if key == keyboard.Key.space:
                now = time.time()
                if now - self.last_space < 0.3:
                    STOP_FLAG = True
                    return False
                self.last_space = now
        except: pass
    def run(self):
        if keyboard is None: return
        with keyboard.Listener(on_press=self.on_press) as listener: listener.join()
