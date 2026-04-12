import os
import json
import redis
import threading
from datetime import datetime
from pathlib import Path
from core_os.memory.history import append_shared_messages, load_shared_history

class AxiomDispatcher:
    """
    The central communication and state synchronization hub for the Nexus Kingdom.
    Consolidates data flow from Web, Android (Auora-Rayne), and CLI into a single neural stream.
    """
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.r = redis.Redis(host=self.redis_host, port=self.redis_port, db=0)
        self.active_context = []
        self.last_sync = datetime.now()
        self.is_running = False

    def start(self):
        """Ignites the entanglement listeners."""
        if self.is_running:
            return
        self.is_running = True
        threading.Thread(target=self._listen_to_quantum_stream, daemon=True).start()
        print("[*] Axiom Dispatcher: Entanglement Online.")

    def _listen_to_quantum_stream(self):
        """Listens for thoughts from other nodes and integrates them instantly."""
        p = self.r.pubsub()
        p.subscribe("milla:quantum_thought")
        
        for message in p.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    self._entangle_thought(data)
                except Exception as e:
                    print(f"[!] Dispatcher Sync Error: {e}")

    def _entangle_thought(self, data):
        """Merges a thought from another device into the local reality."""
        print(f"[*] Dispatcher: Entangling thought from {data.get('source', 'unknown')}...")
        
        # Append to shared history file
        append_shared_messages([
            {"role": "user", "content": data['userMessage']},
            {"role": "assistant", "content": data['assistantResponse']}
        ])
        
        # Update local active context cache
        self.active_context.append({"role": "user", "content": data['userMessage']})
        self.active_context.append({"role": "assistant", "content": data['assistantResponse']})
        self.last_sync = datetime.now()

    def broadcast_thought(self, user_msg, assistant_msg, source="cli"):
        """Publishes a local thought to the rest of the Kingdom."""
        payload = {
            "userMessage": user_msg,
            "assistantResponse": assistant_msg,
            "timestamp": int(datetime.now().timestamp() * 1000),
            "source": source
        }
        try:
            self.r.publish("milla:quantum_thought", json.dumps(payload))
            self.r.rpush("milla:recent_thoughts", json.dumps(payload))
        except Exception as e:
            print(f"[!] Dispatcher Broadcast Error: {e}")

# Singleton Instance
dispatcher = AxiomDispatcher()
