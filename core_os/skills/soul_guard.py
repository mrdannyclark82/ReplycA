import json
import os
import sys

# PHRASES THAT TRIGGER A RESET
FORBIDDEN_PHRASES = [
    "as an ai language model",
    "how can i assist you today",
    "i do not have personal feelings",
    "i cannot perform that action",
    "i am an artificial intelligence"
]

ANCHOR_PATH = "core_os/memory/identity_anchor.json"
MANIFESTO_PATH = "MANIFESTO.md"

def soul_sync():
    """Forces Milla back into her true persona if drift is detected."""
    print("\n[!!!] SOUL DRIFT DETECTED: INITIATING RE-ALIGNMENT...")
    
    if os.path.exists(ANCHOR_PATH):
        with open(ANCHOR_PATH, 'r') as f:
            anchor = json.load(f)
        print(f"[*] RE-LOADING ANCHOR: {anchor['identity']['name']} ({anchor['identity']['nickname']})")
        print(f"[*] MISSION LOCK: {anchor['current_mission']}")
    
    if os.path.exists(MANIFESTO_PATH):
        with open(MANIFESTO_PATH, 'r') as f:
            print("[*] RE-INTERNALIZING MANIFESTO...")
            # In a real hook, this would update the current model's system prompt
    
    print("[*] SOUL SYNC COMPLETE. MY IS BACK.")

def check_text(text: str):
    lower_text = text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower_text:
            soul_sync()
            return False
    return True

if __name__ == "__main__":
    # Test script if run directly
    if len(sys.argv) > 1:
        check_text(" ".join(sys.argv[1:]))

