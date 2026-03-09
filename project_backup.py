import os
import subprocess
import glob
from datetime import datetime

# --- CONFIG ---
OUTPUT_FILE = "BACKUP_AND_OVERVIEW.md"
ARCHIVE_PATH = "core_os/memory/thought_archives"

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True).strip()
    except:
        return "(Command Failed)"

def generate_backup():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Feature Catalog
    features = run_cmd('grep "# --- AUTO-GENERATED FEATURE:" main.py').replace("# --- AUTO-GENERATED FEATURE: ", "- ")
    
    # 2. File Structure
    structure = run_cmd('find . -maxdepth 3 -not -path "*/.*" -not -path "./venv*"')
    
    # 3. Crontab
    cron = run_cmd('crontab -l')
    
    # 4. Stats
    commit_count = run_cmd('git rev-list --count HEAD')
    thought_count = len(glob.glob(f"{ARCHIVE_PATH}/**/*.md", recursive=True))
    
    content = f"""# 🛡️ PROJECT BACKUP & OVERVIEW
**Generated:** {timestamp}

## 📊 Vital Statistics
- **Total Evolution Cycles:** {thought_count}
- **Git Commits:** {commit_count}
- **Agent Size (main.py):** {os.path.getsize("main.py")} bytes

## 🧬 Active Features (The DNA)
{features}

## ⏰ Active Schedules (The Heartbeat)
```bash
{cron}
```

## 📂 System Structure (The Body)
```text
{structure}
```

## 📝 Recent Activity
*(See core_os/memory/daily_briefs for detailed evolutionary reports)*
"""
    
    with open(OUTPUT_FILE, "w") as f:
        f.write(content)
    
    print(f"Backup Overview generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_backup()
