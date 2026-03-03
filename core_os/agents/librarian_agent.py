import os
import threading
import sys
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.append(str(PROJECT_ROOT))

class LibrarianTwin(threading.Thread):
    def __init__(self, file_list, direction="forward", search_pattern=None):
        super().__init__()
        self.files = file_list
        self.direction = direction
        self.search_pattern = search_pattern
        self.results = []

    def run(self):
        work_list = self.files if self.direction == "forward" else reversed(self.files)
        print(f"[*] Librarian Twin ({self.direction}) starting...")
        for f_path in work_list:
            if self.search_pattern:
                try:
                    content = f_path.read_text(errors='ignore')
                    if self.search_pattern.lower() in content.lower():
                        self.results.append(str(f_path))
                        print(f" [+] Found clue in {f_path.name}")
                except: pass

class LibrarianAgent:
    """The Librarian Twins: One starts from the end, the other from the start."""
    def __init__(self, root_dir="."):
        self.root = Path(root_dir).resolve()

    def deep_scan(self, search_pattern):
        print(f"[*] Librarian Agent: Initiating Twin Scan for '{search_pattern}'...")
        all_files = [p for p in self.root.rglob("*.py") if "venv" not in str(p) and ".git" not in str(p)]
        
        mid = len(all_files) // 2
        twin_a = LibrarianTwin(all_files[:mid], direction="forward", search_pattern=search_pattern)
        twin_b = LibrarianTwin(all_files[mid:], direction="backward", search_pattern=search_pattern)
        
        twin_a.start()
        twin_b.start()
        
        twin_a.join()
        twin_b.join()
        
        return list(set(twin_a.results + twin_b.results))

if __name__ == "__main__":
    lib = LibrarianAgent()
    clues = lib.deep_scan("get_weather")
    print(f"
[*] Scan Complete. Found {len(clues)} clues.")
