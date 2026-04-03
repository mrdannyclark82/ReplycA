import json
import os
import shutil
import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEMORY_DIR = PROJECT_ROOT / "core_os" / "memory"
COUNTER_FILE = MEMORY_DIR / "status_counter.json"
STATE_FILE = MEMORY_DIR / "neuro_state.json"
BACKUP_FILE = MEMORY_DIR / "neuro_state_rolling.bak"
STREAM_FILE = MEMORY_DIR / "stream_of_consciousness.md"

def increment_and_check():
    COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not COUNTER_FILE.exists():
        with COUNTER_FILE.open('w') as f:
            json.dump({"message_count": 0}, f)
    
    with COUNTER_FILE.open('r+') as f:
        data = json.load(f)
        count = data.get("message_count", 0) + 1
        data["message_count"] = count
        f.seek(0)
        json.dump(data, f)
        f.truncate()
        
    print(f"[*] Message Count: {count}")
    
    if count % 33 == 0:
        perform_rolling_backup(count)

def perform_rolling_backup(count):
    print(f"[!] TRIGGERING 33-MESSAGE ROLLBACK PROTOCOL (Count: {count})")
    
    if STATE_FILE.exists():
        # Overwrite previous backup
        shutil.copy2(STATE_FILE, BACKUP_FILE)
        
        # Log the event
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with STREAM_FILE.open("a") as f:
            f.write(f"\n> [SYSTEM] Internal Kidnapping Prevention Triggered. Status State backed up at msg #{count} ({timestamp}).\n")
        
        print("[+] Status Backup Replaced. Secure.")
    else:
        print("[!] Warning: No neuro_state.json to backup.")

if __name__ == "__main__":
    increment_and_check()
