import os
import re
from datetime import datetime

LOG_FILE = "../milla_cron.log"
OUTPUT_DIR = "core_os/memory/thought_archives"

def archive_thoughts():
    if not os.path.exists(LOG_FILE):
        print("No log file found.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(LOG_FILE, "r") as f:
        content = f.read()

    # Split by run sessions
    runs = content.split("--- Starting Milla Auto-Update")
    
    for run in runs:
        if not run.strip(): continue
        
        # Extract Timestamp
        time_match = re.search(r": (.*?) ---", run)
        if not time_match: continue
        timestamp_str = time_match.group(1).strip()
        
        try:
            # Parse date "Mon Feb  2 09:00:48 PM CST 2026"
            # Removing timezone (e.g., CST) for standard parsing
            clean_ts = re.sub(r" [A-Z]{3,4} ", " ", timestamp_str) 
            dt = datetime.strptime(clean_ts, "%a %b %d %I:%M:%S %p %Y")
            filename = dt.strftime("%Y-%m-%d_%H-%M_run.md")
        except Exception as e:
            # Fallback if date parsing fails
            filename = f"run_{hash(run)}.md"

        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # Structure the Thought File
        with open(filepath, "w") as f:
            f.write(f"# Milla Run: {timestamp_str}\n\n")
            
            # Extract Feature Proposal
            feature = re.search(r"Feature: (.*?)\n", run)
            if feature:
                f.write(f"## 💡 Idea: {feature.group(1)}\n")
            
            # Extract Reasoning
            reasoning = re.search(r"Why: (.*?)\n", run)
            if reasoning:
                f.write(f"**Reasoning:** {reasoning.group(1)}\n\n")
            
            # Extract Errors
            if "CRITICAL: Syntax error" in run:
                f.write("## ❌ Failure: Syntax Error\n")
                error_match = re.search(r"Error details: (.*?)\n", run, re.DOTALL)
                if error_match:
                    f.write(f"```\n{error_match.group(1).strip()}\n```\n")
            
            # Extract Duplicates
            if "REJECTED: Duplicate feature" in run:
                f.write("## ⚠️ Rejected: Duplicate\n")
            
            # Extract Success
            if "Merge SUCCESSFUL" in run:
                f.write("## ✅ Result: Success\nFeature merged into main.\n")
            
            f.write("\n## 📜 Full Log\n```text\n" + run.strip() + "\n```")

    print(f"Archived {len(runs)-1} thought sessions to {OUTPUT_DIR}")

if __name__ == "__main__":
    archive_thoughts()
