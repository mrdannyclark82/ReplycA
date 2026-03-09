import sqlite3
import os
from datetime import datetime
from pathlib import Path

# --- CENTRALIZED PATHS ---
# These are absolute paths based on the location of this file
MEMORY_DIR = Path(__file__).parent.resolve()
CORE_OS_DIR = MEMORY_DIR.parent
PROJECT_ROOT = CORE_OS_DIR.parent

# Database & Index Paths
DB_PATH = MEMORY_DIR / "agent_memory.db"
CATALOG_PATH = MEMORY_DIR / "agent_memory.db"
LONG_TERM_DB = MEMORY_DIR / "milla_long_term.db"
SEMANTIC_INDEX = MEMORY_DIR / "semantic_index.json"
GRAPH_FILE = MEMORY_DIR / "knowledge_graph.json"
NEURO_FILE = MEMORY_DIR / "neuro_state.json"
STREAM_FILE = MEMORY_DIR / "stream_of_consciousness.md"
IDENTITY_ANCHOR = MEMORY_DIR / "identity_anchor.json"
HISTORICAL_FILE = MEMORY_DIR / "historical_knowledge.json"
WEATHER_CACHE = MEMORY_DIR / "weather_cache.json"
GIM_JOURNAL_PATH = MEMORY_DIR / "gim_journal.md"
ARCHIVE_PATH = MEMORY_DIR / "thought_archives"
DREAM_LOG = MEMORY_DIR / "dreams.txt"
MEMORY_PATH = MEMORY_DIR / "shared_chat.jsonl"

# Asset Paths
SCREENSHOTS_DIR = CORE_OS_DIR / "screenshots"
SCAN_PNG = SCREENSHOTS_DIR / "scan.png"
DYNAMIC_TOOLS_DIR = CORE_OS_DIR / "dynamic_tools"
MEDIA_DIR = CORE_OS_DIR / "media"
LATEST_SPEECH = MEDIA_DIR / "latest_speech.mp3"

class AgentMemory:
    def __init__(self, db_path=str(DB_PATH)):
        # Ensure directories exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(str(SCREENSHOTS_DIR), exist_ok=True)
        os.makedirs(str(DYNAMIC_TOOLS_DIR), exist_ok=True)
        os.makedirs(str(MEDIA_DIR), exist_ok=True)
        os.makedirs(str(ARCHIVE_PATH), exist_ok=True)
        
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Core Memory Table
        self.cursor.execute('CREATE TABLE IF NOT EXISTS mem (k TEXT PRIMARY KEY, v TEXT, t DATETIME)')
        
        # Card Catalog Table (The Library's Index)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                path TEXT,
                line INTEGER,
                type TEXT,
                timestamp DATETIME
            )
        ''')

        # Mailbox Table (Remote Node Queuing)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS mailbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                role TEXT,
                content TEXT,
                status TEXT DEFAULT 'pending',
                timestamp DATETIME
            )
        ''')
        self.conn.commit()

    def remember(self, key, value):
        self.cursor.execute("INSERT OR REPLACE INTO mem VALUES (?, ?, ?)", (key, value, datetime.now()))
        self.conn.commit()
        return f"Memory Locked: {key}"

    def recall(self, key):
        self.cursor.execute("SELECT v FROM mem WHERE k=?", (key,))
        res = self.cursor.fetchone()
        return res[0] if res else "None."

    # Mailbox Methods
    def post_mail(self, target, role, content):
        """Posts a message to the mailbox for a remote node."""
        self.cursor.execute(
            "INSERT INTO mailbox (target, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (target, role, content, datetime.now())
        )
        self.conn.commit()

    def fetch_mail(self, target, clear=True):
        """Fetches all pending mail for a target."""
        self.cursor.execute(
            "SELECT id, role, content, timestamp FROM mailbox WHERE target=? AND status='pending'",
            (target,)
        )
        messages = self.cursor.fetchall()
        if messages and clear:
            # Mark as delivered
            self.cursor.execute(
                "UPDATE mailbox SET status='delivered' WHERE target=? AND status='pending'",
                (target,)
            )
            self.conn.commit()
        return messages

    # Card Catalog Methods
    def register_symbol(self, name, path, line, s_type):
        self.cursor.execute(
            "INSERT OR REPLACE INTO catalog (symbol, path, line, type, timestamp) VALUES (?, ?, ?, ?, ?)",
            (name, path, line, s_type, datetime.now())
        )
        self.conn.commit()

    def search_catalog(self, pattern):
        self.cursor.execute(
            "SELECT symbol, path, line, type FROM catalog WHERE symbol LIKE ?",
            (f"%{pattern}%",)
        )
        return self.cursor.fetchall()

    def clear_catalog(self):
        self.cursor.execute("DELETE FROM catalog")
        self.conn.commit()

# Singleton instance
memory = AgentMemory()
