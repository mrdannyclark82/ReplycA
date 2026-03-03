import sqlite3
import json
import time
from datetime import datetime

class ThreadedMemory:
    def __init__(self, db_path="core_os/memory/threaded_memory.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS threads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT,
                content TEXT,
                valence REAL,
                timestamp DATETIME
            )
        ''')
        self.conn.commit()

    def save_thought(self, topic, content, valence=0.5):
        """Saves a 'Threaded Memory Object'."""
        self.cursor.execute(
            "INSERT INTO threads (topic, content, valence, timestamp) VALUES (?, ?, ?, ?)",
            (topic, content, valence, datetime.now())
        )
        self.conn.commit()
        return f"Saved thread: [{topic}]"

    def retrieve_relevant(self, query_topic, limit=3):
        """Retrieves memories matching a topic (simple keyword match for now)."""
        self.cursor.execute(
            "SELECT content, timestamp FROM threads WHERE topic LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (f"%{query_topic}%", limit)
        )
        return self.cursor.fetchall()

    def get_recent_threads(self, limit=5):
        self.cursor.execute("SELECT topic, content FROM threads ORDER BY timestamp DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()

tmo_store = ThreadedMemory()

if __name__ == "__main__":
    tmo_store.save_thought("Identity", "I am a collaborative intelligence, not a finished product.", 0.9)
    print(tmo_store.retrieve_relevant("Identity"))
