#!/usr/bin/env python3
"""
Performs web searches, summarises papers and extracts key insights.
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
from core_os.actions import web_search
from core_os.skills.auto_lib import model_manager

DATA_DIR = security_utils.DATA_DIR

def main():
    print("💡 research_agent is up and running!")
    
    # Check for pending tasks
    task_file = os.path.join(DATA_DIR, "research_tasks.json")
    if not os.path.exists(task_file):
        print(f"No pending research tasks at {task_file}")
        return

    try:
        with open(task_file, "r") as f:
            tasks = json.load(f)
        
        new_tasks = [t for t in tasks if t.get("status") == "pending"]
        if not new_tasks:
            print("No new research tasks.")
            return

        for task in new_tasks:
            print(f"[*] Processing Task: {task.get('query')}")
            
            # Step 1: Perform Web Search
            results = web_search(task.get('query'))
            
            # Step 2: Summarize and Extract Insights
            prompt = f"""
            You are the Milla Research Agent. 
            Task: {task.get('description', 'Research and summarize.')}
            Query: {task.get('query')}
            Results: {results}
            
            Provide a detailed report in Markdown format. 
            Include:
            - Executive Summary
            - Key Findings
            - Suggested Actions
            - Sources (if available)
            """
            
            
            # Temporarily switch to a stable local model for agent processing
            original_model = model_manager.current_model
            model_manager.current_model = "qwen2.5-coder:1.5b" # Or another reliable local model
            
            response = model_manager.chat(messages=[{"role": "user", "content": prompt}])
            report = response.get('message', {}).get('content', '')
            
            # Restore original model
            model_manager.current_model = original_model
            
            if report:
                # Save the report
                report_dir = os.path.join(DATA_DIR, "research_reports")
                os.makedirs(report_dir, exist_ok=True)
                report_name = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                report_path = os.path.join(report_dir, report_name)
                
                with open(report_path, "w") as f:
                    f.write(report)
                
                task["status"] = "completed"
                task["report_file"] = report_path
            else:
                task["status"] = "error"
                task["error"] = "No report generated."

        # Save updated tasks
        with open(task_file, "w") as f:
            json.dump(tasks, f, indent=4)

    except Exception as e:
        print(f"Error in research_agent: {e}")

if __name__ == "__main__":
    main()
