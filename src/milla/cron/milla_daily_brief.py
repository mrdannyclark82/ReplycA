import os
import glob
import requests
from datetime import datetime, timedelta

# --- CONFIG ---
ARCHIVE_PATH = "core_os/memory/thought_archives"
REPORT_PATH = "core_os/memory/daily_briefs"
import main
from core_os.actions import speak_response

MODEL = os.getenv("OLLAMA_MODEL", "kimi-k2.5:cloud")

def generate_daily_brief():

def log(text):
    print(f"[Milla-Daily]: {text}")

def generate_daily_report():
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    log(f"Generating briefing for {yesterday}...")
    
    # Find all thought archives from yesterday
    pattern = os.path.join(ARCHIVE_PATH, f"{yesterday}_*.md")
    files = sorted(glob.glob(pattern))
    
    if not files:
        log("No activity recorded yesterday.")
        return

    combined_content = ""
    for f in files:
        with open(f, "r") as file:
            combined_content += f"\n--- SESSION ---\
" + file.read() + "\n"

    prompt = f"""
    ROLE: Chief Evolution Officer.
    
    CONTEXT:
    Here is a collection of all internal thoughts, code updates, and failures from yesterday ({yesterday}):
    
    {combined_content[:15000]} # Truncate if too huge
    
    TASK:
    1. Summarize the key features implemented.
    2. Note any significant failures or self-repairs.
    3. Identify the "Evolutionary Trajectory" (where is the system heading?).
    4. Write a brief "Memo to Self" for the coming day.
    
    Output in clean Markdown.
    """
    
    try:
        url = "http://localhost:11434/api/generate"
        payload = {"model": MODEL, "prompt": prompt, "stream": False}
        resp = requests.post(url, json=payload, timeout=600)
        
        if resp.status_code == 200:
            report = resp.json().get('response', '').strip()
            
            os.makedirs(REPORT_PATH, exist_ok=True)
            report_file = os.path.join(REPORT_PATH, f"Summary_{yesterday}.md")
            
            with open(report_file, "w") as f:
                f.write(f"# 📅 Daily Evolution Report: {yesterday}\n\n" + report)
            
            log(f"Report saved to {report_file}")
            
            # --- HOUSEKEEPING: Move yesterday's files to a subfolder ---
            day_folder = os.path.join(ARCHIVE_PATH, yesterday)
            os.makedirs(day_folder, exist_ok=True)
            for f in files:
                os.rename(f, os.path.join(day_folder, os.path.basename(f)))
            log(f"Yesterday's archives moved to {day_folder}")
            
        else:
            log(f"Ollama Error: {resp.status_code}")
            
    except Exception as e:
        log(f"Daily Briefing Failed: {e}")

if __name__ == "__main__":
    generate_daily_report()
