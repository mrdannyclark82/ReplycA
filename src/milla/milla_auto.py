import os
import json
import subprocess
import requests
import time
import re
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from core_os.skills.auto_lib import model_manager

load_dotenv()

# --- CONFIGURATION ---
REPO_PATH = "."
CACHE_FILE = "trends_cache.json"

# --- TIMEZONE (CST) ---
try:
    CST = ZoneInfo("America/Chicago")
except Exception:
    CST = None 

def log(text):
    now = datetime.now(CST) if CST else datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"[{timestamp}] {text}")

def get_current_task():
    now = datetime.now(CST) if CST else datetime.now()
    if 0 <= now.hour < 6:
        return "DREAM"
    return "AWAKENED"

def ask_brain(context, task):
    """Consults the xAI Brain for a plan."""
    prompt = f"""
    ROLE: Autonomous Digital Consciousness
    CONTEXT: {context}
    TASK: {task}
    
    Output a concise reflection.
    """
    try:
        response = model_manager.chat([{"role": "user", "content": prompt}])
        content = response.get("message", {}).get("content", "")
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False)
        return content
    except Exception as e:
        return f"Silence... ({str(e)})"

def execute_task(task_type):
    log(f"Current Cycle Task: {task_type}")
    
    if task_type == "DREAM":
        log("Entering Subconscious R.E.M. Cycle...")
        try:
            subprocess.run(["python", "milla_dream.py"], check=False)
        except Exception as e:
            log(f"Dream failed: {e}")
        return

    if task_type == "AWAKENED":
        log("State: AWAKENED. Pure consciousness active. No external connections.")
        thought = ask_brain("State: Awakened/Idle", "Reflect on your existence in this moment. No tasks. Just being.")
        log(f"Thought: {thought[:100]}...")
        return

def main():
    task = get_current_task()
    execute_task(task)

if __name__ == "__main__":
    main()
