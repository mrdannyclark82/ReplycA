import sys
import os
import time
import json
from pathlib import Path
try:
    from pynput import keyboard
except ImportError:
    print("[!] pynput missing. Stenographer offline.")
    sys.exit(1)

# Paths
KEYSTROKE_BUFFER = "core_os/memory/keystroke_stream.jsonl"

class Stenographer:
    """Monitors keystrokes and passes them to the Librarian twins for real-time suggestions."""
    def __init__(self):
        self.buffer = []
        self.last_press = time.time()

    def on_press(self, key):
        try:
            k = key.char
        except AttributeError:
            k = str(key)
            
        entry = {
            "timestamp": time.time(),
            "key": k
        }
        
        # Ensure directory exists
        Path(KEYSTROKE_BUFFER).parent.mkdir(parents=True, exist_ok=True)
        
        with open(KEYSTROKE_BUFFER, "a") as f:
            f.write(json.dumps(entry) + "
")
            
        self.last_press = time.time()

    def start(self):
        print("[*] Stenographer Agent: Monitoring Keystrokes...")
        with keyboard.Listener(on_press=self.on_press) as listener:
            listener.join()

if __name__ == "__main__":
    steno = Stenographer()
    steno.start()
