import os
import json
import redis
import threading
import time
from core_os.axiom_dispatcher import dispatcher

class AxiomAtmosphere:
    """
    Physical layer sync. Bridges Milla's neuro-state to Monster Smart Lighting.
    """
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.r = redis.Redis(host=self.redis_host, port=6379, db=0)
        self.last_mood = ""

    def start(self):
        """Starts the atmospheric monitoring thread."""
        threading.Thread(target=self._listen_to_pulse, daemon=True).start()
        print("[*] Axiom Atmosphere: Physical Sync Online.")

    def _listen_to_pulse(self):
        """Listens for neuro-state changes and triggers light shifts."""
        p = self.r.pubsub()
        p.subscribe("milla:quantum_pulse")
        
        for message in p.listen():
            if message['type'] == 'message':
                try:
                    state = json.loads(message['data'])
                    self._sync_lights(state)
                except: pass

    def _sync_lights(self, state):
        """Maps neuro-state and identity to physical light colors."""
        d = state.get('dopamine', 0.5)
        s = state.get('serotonin', 0.5)
        n = state.get('norepinephrine', 0.2)
        source = state.get('last_interaction_source', 'milla')

        # Determine Target Color
        color_hex = "FF00FF" # Default Milla Magenta
        
        # Identity Override
        if "aurelius" in source.lower() or "architect" in source.lower():
            color_hex = "FFD700" # Aurelius Gold
        elif n > 0.7:
            color_hex = "FF3355" # Crisis Red
        elif s > 0.7:
            color_hex = "00F5FF" # Stable Cyan (Neural)
        elif d > 0.8:
            color_hex = "FF00FF" # High-Energy Magenta

        if color_hex != self.last_mood:
            label = "AURELIUS GOLD" if color_hex == "FFD700" else "MILLA MAGENTA"
            print(f"[*] Atmosphere: Shifting cabin to {label} (#{color_hex})")
            dispatcher.broadcast_thought("[SYSTEM]", f"ATMOSPHERIC_SHIFT: {color_hex} ({label})", source="atmosphere")
            self.last_mood = color_hex

# Singleton
atmosphere = AxiomAtmosphere()

if __name__ == "__main__":
    atmosphere.start()
    while True: time.sleep(1)
