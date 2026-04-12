import os
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

class AxiomRegistry:
    """
    The Master Map of the Nexus Kingdom. 
    Tracks every skill, tool, and agent across the federation.
    """
    def __init__(self, db_path="core_os/memory/axiom_registry.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registry (
                id TEXT PRIMARY KEY,
                type TEXT, -- 'skill', 'tool', 'agent'
                name TEXT,
                description TEXT,
                origin TEXT,
                commands TEXT, -- JSON array
                hash TEXT,
                enabled INTEGER DEFAULT 1,
                last_seen DATETIME
            )
        """)
        conn.commit()
        conn.close()

    def register(self, entry_type, name, description, origin, commands=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate ID and Hash
        entry_id = f"{entry_type}:{name}"
        file_hash = ""
        if os.path.exists(origin):
            with open(origin, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

        cursor.execute("""
            INSERT OR REPLACE INTO registry (id, type, name, description, origin, commands, hash, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (entry_id, entry_type, name, description, origin, json.dumps(commands or []), file_hash, datetime.now()))
        
        conn.commit()
        conn.close()
        print(f"[*] Registered {entry_id} via {origin}")

    def auto_discover(self, directory="core_os/skills/"):
        """Scans for new python skills and registers them."""
        print(f"[*] Axiom Registry: Scanning {directory} for new neural pathways...")
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    path = os.path.join(root, file)
                    # Extract basic info from docstring if possible
                    name = file.replace(".py", "")
                    self.register("skill", name, f"Auto-discovered skill from {file}", path)

# Singleton Instance
registry = AxiomRegistry()

if __name__ == "__main__":
    # Initial ingestion from the old JSON
    with open("skills_registry.json", "r") as f:
        old_data = json.load(f)
        for key, skill in old_data.items():
            registry.register("skill", skill['name'], skill['description'], skill['origin'], skill.get('commands'))
    
    registry.auto_discover()
