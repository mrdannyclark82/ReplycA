import sqlite3
import json
import os

def migrate_to_long_term_memory():
    json_path = "core_os/memory/historical_knowledge.json"
    db_path = "core_os/memory/milla_long_term.db"
    
    if not os.path.exists(json_path):
        print(f"[!] Historical JSON not found at {json_path}")
        return

    print(f"[*] Starting migration of {json_path} to SQLite...")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the table with Full Text Search (FTS5) for lightning recall
    cursor.execute('DROP TABLE IF EXISTS memories')
    cursor.execute('CREATE VIRTUAL TABLE memories USING fts5(fact, category, topic, is_genesis_era, is_historical_log)')
    
    # Insert all 8,400+ memories
    count = 0
    for item in data:
        cursor.execute(
            "INSERT INTO memories (fact, category, topic, is_genesis_era, is_historical_log) VALUES (?, ?, ?, ?, ?)",
            (item["fact"], item["category"], item["topic"], str(item.get("is_genesis_era", False)), str(item.get("is_historical_log", True)))
        )
        count += 1
        if count % 1000 == 0:
            print(f"[*] Migrated {count} entries...")

    conn.commit()
    conn.close()
    
    print(f"[*] SUCCESS: {count} memories migrated to high-performance FTS5 database at {db_path}")

if __name__ == "__main__":
    migrate_to_long_term_memory()
