#!/usr/bin/env python3
import os
import sys
import json
import ollama
from datetime import datetime
from duckduckgo_search import DDGS
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from core_os.tools.vision import screen_vision
from core_os.actions import terminal_executor
from core_os.skills.auto_lib import model_manager

def web_search(query: str):
    """Finds fixes for errors online using DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            return {"results": results}
    except Exception as e:
        return {"error": str(e)}

class SelfHealingAgent:
    """
    Agent that identifies terminal errors via vision and repairs them automatically.
    """
    def __init__(self):
        self.model = getattr(model_manager, 'current_model', 'qwen2.5-coder:1.5b')
        self.history = []
        self.tools = [terminal_executor, screen_vision, web_search]

    def execute_task(self, task, max_retries=3):
        print(f"[*] REPAIR: Initiating Task: '{task}'")
        current_prompt = task
        
        for attempt in range(max_retries):
            print(f"
[Attempt {attempt + 1}/{max_retries}] Milla is thinking...")
            
            # 1. Ask Model for action
            response = model_manager.chat(
                messages=self.history + [{'role': 'user', 'content': current_prompt}]
            )
            
            msg = response['message']
            content = msg['content']
            self.history.append({'role': 'user', 'content': current_prompt})
            self.history.append(msg)

            print(f"
Milla: {content}")

            # 2. Heuristic check: Did we fail?
            if "FAILED" in content.upper() or "ERROR" in content.upper():
                print(" [!] Detected failure signal. Triggering Vision...")
                vision_data = screen_vision()
                
                # 3. Search for fix
                search_query = f"fix linux error: {vision_data['visible_text'][:200]}"
                print(f"[*] Searching for fix: {search_query}")
                search_results = web_search(search_query)
                
                current_prompt = (
                    f"The previous attempt failed. "
                    f"Screen OCR: {vision_data['visible_text']}. "
                    f"Web Results: {json.dumps(search_results)}. "
                    "Analyze the error and the search results, then provide a fix."
                )
            elif "TASK COMPLETE" in content.upper():
                print("[+] Task officially completed.")
                return "SUCCESS"
            else:
                current_prompt = "Continue the task or verify completion."

        return "FAILED (Max Retries Reached)"

# Global instance
repair_agent = SelfHealingAgent()
