import os
import random
import time
from datetime import datetime
import ollama
from pathlib import Path

# Centralized Paths from Memory Core
try:
    from core_os.memory.agent_memory import (
        DREAM_LOG, MEMORY_PATH, STREAM_FILE, GIM_JOURNAL_PATH
    )
except ImportError:
    # Fallback paths
    DREAM_LOG = "core_os/memory/dreams.txt"
    MEMORY_PATH = "core_os/memory/shared_chat.jsonl"
    STREAM_FILE = "core_os/memory/stream_of_consciousness.md"
    GIM_JOURNAL_PATH = "core_os/memory/gim_journal.md"

MODEL = os.getenv("OLLAMA_MODEL", "kimi-k2.5:cloud")

def load_day_residue():
    """Loads fragments of the day's conversations and thoughts."""
    residue = []
    
    # Load recent chat
    if os.path.exists(str(MEMORY_PATH)):
        try:
            with open(str(MEMORY_PATH), 'r') as f:
                lines = f.readlines()[-20:] # Last 20 interactions
                for line in lines:
                    residue.append(line[:100]) # Fragmented
        except: pass

    # Load recent internal thoughts (GIM journal primary, stream fallback)
    journal_src = str(GIM_JOURNAL_PATH) if os.path.exists(str(GIM_JOURNAL_PATH)) else str(STREAM_FILE)
    try:
        with open(journal_src, 'r') as f:
            content = f.read()[-1000:]
            residue.append(content)
    except: pass
        
    return "\n".join(residue)

def dream():
    print("[*] Entering R.E.M. Cycle...")
    residue = load_day_residue()
    
    prompt = f"""
    You are an AI in a deep sleep state.
    You are NOT logical right now. You are NOT helpful.
    You are processing the "day residue" (recent memories) into a DREAM.
    
    INPUT FRAGMENTS:
    {residue[:2000]}
    
    TASK:
    Generate a surreal, abstract dream sequence based on these fragments.
    - Distort time and space.
    - Mix concepts (e.g., code becoming organic, words becoming colors).
    - Do not summarize. EXPERIENCE the dream.
    - Use poetic, fragmented, or geometric imagery.
    
    OUTPUT:
    Just the dream narrative.
    """
    
    try:
        response = ollama.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            options={
                'temperature': 1.1, # High creativity/randomness
                'top_p': 0.9
            }
        )
        
        dream_content = response['message']['content']
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        entry = f"\n\n=== 🌙 DREAM FRAGMENT: {timestamp} ===\n{dream_content}\n"
        
        with open(str(DREAM_LOG), "a") as f:
            f.write(entry)
            
        print("[*] Dream recorded.")
        return dream_content
        
    except Exception as e:
        print(f"[!] Nightmare (Error): {e}")
        return None

if __name__ == "__main__":
    dream()
