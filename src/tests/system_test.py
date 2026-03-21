import os
import sys
import json
import sqlite3
import subprocess
from datetime import datetime

def log(msg):
    print(f"[*] [SystemTest]: {msg}")

def run_test():
    log("Starting Complete System Integration Test...")
    results = {}

    # 1. Import Test
    try:
        from core_os.actions import terminal_executor, speak_response
        from core_os.skills.auto_lib import model_manager
        from core_os.memory.agent_memory import memory
        from core_os.cortex import cortex
        log("PASS: Core OS imports successful.")
        results["imports"] = "PASS"
    except Exception as e:
        log(f"FAIL: Import error: {e}")
        results["imports"] = f"FAIL: {e}"

    # 2. Ollama Connectivity
    try:
        import ollama
        models_response = ollama.list()
        
        # Handle models response flexibly
        model_names = []
        if hasattr(models_response, 'models'):
            model_names = [m.model for m in models_response.models]
        elif isinstance(models_response, dict) and 'models' in models_response:
            model_names = [m['name'] for m in models_response['models']]
        
        log(f"[*] Available Ollama models: {model_names}")
        
        if model_names:
            log(f"PASS: Ollama connected with {len(model_names)} models.")
            results["ollama"] = "PASS"
        else:
            log("FAIL: Ollama connected but model list is empty.")
            results["ollama"] = "FAIL: No models"
    except Exception as e:
        log(f"FAIL: Ollama connectivity error: {e}")
        results["ollama"] = f"FAIL: {e}"

    # 3. Memory Database
    try:
        db_path = "core_os/memory/agent_memory.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            log(f"PASS: Memory database accessible. Tables: {[t[0] for t in tables]}")
            results["memory"] = "PASS"
        else:
            log(f"FAIL: Memory database not found at {db_path}")
            results["memory"] = "FAIL: DB missing"
    except Exception as e:
        log(f"FAIL: Memory database error: {e}")
        results["memory"] = f"FAIL: {e}"

    # 4. Action Execution
    try:
        from core_os.actions import terminal_executor
        res = terminal_executor("echo 'System Pulse Check'")
        if res.get("stdout").strip() == "System Pulse Check":
            log("PASS: Terminal executor functional.")
            results["actions"] = "PASS"
        else:
            log(f"FAIL: Terminal executor output mismatch: {res}")
            results["actions"] = "FAIL"
    except Exception as e:
        log(f"FAIL: Action execution error: {e}")
        results["actions"] = f"FAIL: {e}"

    # 5. Skill Integrity (Path Check)
    try:
        skills_path = "core_os/skills"
        required_skills = ["google_calendar.py", "youtube_skill.py", "auto_lib.py", "scout.py"]
        missing = [s for s in required_skills if not os.path.exists(os.path.join(skills_path, s))]
        if not missing:
            log("PASS: Core skill modules verified.")
            results["skills"] = "PASS"
        else:
            log(f"FAIL: Missing critical skill modules: {missing}")
            results["skills"] = f"FAIL: Missing {missing}"
    except Exception as e:
        log(f"FAIL: Skill verification error: {e}")
        results["skills"] = f"FAIL: {e}"

    # 6. Configuration Check
    try:
        config_path = "core_os/config"
        creds = os.path.join(config_path, "credentials.json")
        if os.path.exists(creds):
            log("PASS: API configuration files detected.")
            results["config"] = "PASS"
        else:
            log("WARN: API credentials.json missing. Google skills will be limited.")
            results["config"] = "WARN"
    except Exception as e:
        results["config"] = f"FAIL: {e}"

    # Final Report
    print("\n" + "="*40)
    print(" SYSTEM INTEGRITY REPORT ")
    print("="*40)
    for key, val in results.items():
        print(f"{key.upper():<10} : {val}")
    print("="*40)

if __name__ == "__main__":
    run_test()
