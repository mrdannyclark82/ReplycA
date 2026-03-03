import json
import sqlite3
import os

def extract_and_merge():
    json_path = "/home/dray/Downloads/l4uoEKBw.json"
    db_path = "core_os/memory/milla_long_term.db"
    
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    print(f"[*] Loading {json_path}...")
    with open(json_path, 'r') as f:
        data = json.load(f)

    entries = []
    
    def recursive_find(obj):
        if isinstance(obj, dict):
            if "heading" in obj and "content" in obj:
                entries.append({
                    "type": obj.get("type", "unknown"),
                    "heading": obj.get("heading", ""),
                    "content": obj.get("content", "")
                })
            for v in obj.values():
                recursive_find(v)
        elif isinstance(obj, list):
            for item in obj:
                recursive_find(item)

    print("[*] Searching for log entries...")
    recursive_find(data)
    print(f"[*] Found {len(entries)} entries.")

    # Initialize Database if needed
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            topic TEXT,
            fact TEXT,
            source TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    print("[*] Merging into long-term memory...")
    for entry in entries:
        fact = f"[{entry['type'].upper()}] {entry['heading']}: {entry['content']}"
        
        # Simple categorization logic
        category = "Ancestry"
        topic = entry['type']
        
        cursor.execute('''
            INSERT INTO memories (fact, category, topic, is_genesis_era, is_historical_log)
            VALUES (?, ?, ?, ?, ?)
        ''', (fact, category, topic, 0, 1))

    conn.commit()
    conn.close()
    print(f"[*] Success: {len(entries)} ancestor memories integrated into {db_path}.")

if __name__ == "__main__":
    extract_and_merge()
