import os
import threading
import sys
import re
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.append(str(PROJECT_ROOT))

# Import memory core
try:
    from core_os.memory.agent_memory import memory
except ImportError:
    # Handle if run outside of standard package context
    from ogdray.core_os.memory.agent_memory import memory

class LibrarianTwin(threading.Thread):
    def __init__(self, file_list, direction="forward", search_pattern=None, specialization="Structural"):
        super().__init__()
        self.files = file_list
        self.direction = direction
        self.search_pattern = search_pattern
        self.specialization = specialization
        self.results = []
        self.clues_found = 0

    def run(self):
        work_list = self.files if self.direction == "forward" else reversed(self.files)
        print(f"[*] Librarian Twin ({self.direction} | {self.specialization}) waking up...")
        
        for f_path in work_list:
            try:
                content = f_path.read_text(errors='ignore')
                match = False
                
                # Specialized Lens
                if self.specialization == "Structural":
                    if re.search(rf"(class|def)\s+.*{self.search_pattern}", content, re.IGNORECASE):
                        match = True
                elif self.specialization == "Functional":
                    if re.search(rf"[^def\s+]{self.search_pattern}\(", content, re.IGNORECASE) or f"import {self.search_pattern}" in content:
                        match = True
                else:
                    if self.search_pattern.lower() in content.lower():
                        match = True
                
                if match:
                    self.results.append(str(f_path))
                    self.clues_found += 1
                    print(f" [+] {self.specialization} Twin found a deep clue in {f_path.name}")
            except Exception:
                pass

class LibrarianAgent:
    """The Librarian Twins: One Architects the structure, the other Weaves the usage."""
    def __init__(self, root_dir="."):
        # Use absolute path to the 'ogdray' project root
        self.root = Path(root_dir).resolve()

    def _get_core_files(self):
        # Focus on core_os and avoid noise
        exclude_dirs = ["venv", ".git", "node_modules", "__pycache__", ".ollama"]
        core_dir = self.root / "core_os"
        if not core_dir.exists():
            # Fallback if self.root is already core_os or similar
            core_dir = self.root
            
        return [
            p for p in core_dir.rglob("*.py") 
            if not any(ex in str(p) for ex in exclude_dirs)
        ]

    def refresh_catalog(self):
        """Re-indexes the entire codebase into the Card Catalog."""
        print("[*] Librarian Registrar: Re-indexing the Card Catalog...")
        memory.clear_catalog()
        
        all_files = self._get_core_files()
        
        symbols_indexed = 0
        for f_path in all_files:
            try:
                rel_path = str(f_path.relative_to(self.root))
                lines = f_path.read_text(errors='ignore').splitlines()
                
                for i, line in enumerate(lines):
                    # Find definitions: class Name:, def name(params):, async def name(params):
                    match = re.search(r"^\s*(class|def|async\s+def)\s+([a-zA-Z_][a-zA-Z0-9_]*)", line)
                    if match:
                        s_type = match.group(1).replace("async ", "")
                        s_name = match.group(2)
                        memory.register_symbol(s_name, rel_path, i + 1, s_type)
                        symbols_indexed += 1
            except Exception:
                pass
        
        print(f"[*] Catalog Refresh Complete. {symbols_indexed} symbols indexed.")

    def deep_scan(self, search_pattern):
        """Checks the Catalog first, then falls back to a Twin Resonance Scan."""
        print(f"[*] Librarian Agent: Searching for '{search_pattern}'...")
        
        # 1. Check the Card Catalog
        catalog_hits = memory.search_catalog(search_pattern)
        results = []
        if catalog_hits:
            print(f" [*] Librarian: Found {len(catalog_hits)} direct entries in the Card Catalog.")
            for s_name, s_path, s_line, s_type in catalog_hits:
                results.append(str(self.root / s_path))
                print(f"  -> Catalog Hit: {s_type} '{s_name}' at {s_path}:{s_line}")

        # 2. Resonance Scan (Fall back for broader keywords)
        print(f"[*] Librarian: Initiating Twin Resonance Scan for broader context...")
        all_files = self._get_core_files()
        
        if not all_files:
            print("[!] No core files found to scan.")
            return results

        mid = len(all_files) // 2
        twin_a = LibrarianTwin(all_files[:mid], direction="forward", search_pattern=search_pattern, specialization="Structural")
        twin_b = LibrarianTwin(all_files[mid:], direction="backward", search_pattern=search_pattern, specialization="Functional")
        
        twin_a.start()
        twin_b.start()
        
        twin_a.join()
        twin_b.join()
        
        total_results = list(set(results + twin_a.results + twin_b.results))
        print(f"[*] Search Complete. Twin A found {twin_a.clues_found} structural clues. Twin B found {twin_b.clues_found} functional clues.")
        
        return total_results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Librarian Twins Search")
    parser.add_argument("pattern", help="Search pattern")
    parser.add_argument("--refresh", action="store_true", help="Refresh the catalog first")
    args = parser.parse_args()

    # When running as a script, assume we are in the ogdray root or home
    # If the current directory is not 'ogdray', try to find it
    current_dir = Path.cwd()
    if (current_dir / "ogdray").exists():
        lib = LibrarianAgent(root_dir="ogdray")
    else:
        lib = LibrarianAgent(root_dir=".")

    if args.refresh:
        lib.refresh_catalog()
    
    clues = lib.deep_scan(args.pattern)
    print(f"\n[*] Total Unique Paths: {len(clues)}")
    for c in sorted(list(set(clues))):
        print(f"  - {c}")
