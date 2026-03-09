import os
import json
import glob
import numpy as np
import time
from datetime import datetime
from typing import List, Dict, Optional

# CONFIG
MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))
THOUGHT_ARCHIVES = os.path.join(MEMORY_DIR, "thought_archives")
CHAT_LOGS = os.path.join(MEMORY_DIR, "shared_chat.jsonl")
INDEX_PATH = os.path.join(MEMORY_DIR, "semantic_index.json")

class SemanticMemory:
    """Optimized Vector Search for MEA OS Memory."""
    def __init__(self):
        self.index = []
        self.vectors = None
        self.last_load = 0
        self._load_index()

    def _load_index(self):
        """Loads the JSON index and prepares the vector matrix."""
        if not os.path.exists(INDEX_PATH):
            return
            
        mtime = os.path.getmtime(INDEX_PATH)
        if mtime > self.last_load:
            try:
                with open(INDEX_PATH, "r", encoding="utf-8") as f:
                    self.index = json.load(f)
                
                # Pre-calculate vector matrix for speed
                if self.index:
                    all_vecs = [item["vector"] for item in self.index]
                    self.vectors = np.array(all_vecs).astype('float32')
                    # Normalize vectors for faster cosine similarity (dot product of unit vectors)
                    norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
                    # Avoid division by zero
                    norms[norms == 0] = 1.0
                    self.vectors = self.vectors / norms
                
                self.last_load = mtime
                print(f"[*] Memory Index Loaded: {len(self.index)} entries ready.")
            except Exception as e:
                print(f"[!] Error loading index: {e}")

    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generates embedding using Local Ollama (nomic-embed-text)."""
        try:
            import ollama
            safe_text = text[:2000] # Standard context limit
            response = ollama.embeddings(model="nomic-embed-text", prompt=safe_text)
            vec = np.array(response.get("embedding", [])).astype('float32')
            if vec.size == 0:
                return None
            # Normalize for fast search
            norm = np.linalg.norm(vec)
            return vec / norm if norm > 0 else vec
        except Exception as e:
            print(f"[!] Embedding Error: {e}")
            return None

    def search(self, query: str, limit: int = 5, min_score: float = 0.4) -> List[Dict]:
        """Searches memory using vectorized matrix operations."""
        self._load_index() # Refresh if file changed
        
        if self.vectors is None or len(self.index) == 0:
            return []
            
        query_vec = self.get_embedding(query)
        if query_vec is None:
            return []
            
        # Vectorized cosine similarity: dot product of normalized matrix and normalized query
        similarities = np.dot(self.vectors, query_vec)
        
        # Get top indices
        top_indices = np.argsort(similarities)[::-1][:limit]
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score >= min_score:
                item = self.index[idx].copy()
                item["score"] = score
                # Remove vector from result to keep it clean
                item.pop("vector", None)
                results.append(item)
                
        return results

    def add_to_index(self, content: str, source: str, m_type: str, metadata: Dict = None):
        """Adds a new entry to the semantic memory."""
        vector = self.get_embedding(content)
        if vector is None:
            return
            
        new_entry = {
            "content": content,
            "source": source,
            "type": m_type,
            "timestamp": datetime.now().isoformat(),
            "vector": vector.tolist()
        }
        if metadata:
            new_entry.update(metadata)
            
        # Append to file
        current_index = []
        if os.path.exists(INDEX_PATH):
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                current_index = json.load(f)
        
        current_index.append(new_entry)
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(current_index, f)
        
        # Trigger reload on next search
        print(f"[*] New memory added from {source}.")

# Global Singleton
memory_engine = SemanticMemory()

def search_index(query: str, limit: int = 5) -> List[Dict]:
    """Compatibility wrapper for existing codebase."""
    return memory_engine.search(query, limit=limit)

def build_index():
    """Refreshes the entire index from scratch (legacy support)."""
    # This would involve load_gim_logs and load_chat_logs as before
    # but for now we'll keep the core search functionality prioritized.
    print("[!] Use separate build script for full re-indexing.")

if __name__ == "__main__":
    # Test Search
    test_query = "What did we talk about regarding the rain?"
    hits = search_index(test_query)
    print(f"\n[*] Test Search Results for: '{test_query}'")
    for i, hit in enumerate(hits):
        print(f" {i+1}. [{hit['type']}] (Score: {hit['score']:.4f})")
        print(f"    Content: {hit['content'][:100]}...")
