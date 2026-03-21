import json
import time
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Try to import centralized paths and memory
try:
    from core_os.memory.agent_memory import (
        memory, STREAM_FILE, NEURO_FILE, LATEST_SPEECH
    )
except ImportError:
    # Fallback paths and mock memory
    STREAM_FILE = "core_os/memory/stream_of_consciousness.md"
    NEURO_FILE = "core_os/memory/neuro_state.json"
    LATEST_SPEECH = "core_os/media/latest_speech.mp3"
    memory = None

import main

HOST = "0.0.0.0"
PORT = 9000
POLL_INTERVAL = 1.0


def _load_lines() -> list[dict]:
    history = main.load_shared_history(limit=10_000)
    return history

def process_background_response(msg):
    """Generates a response in a separate thread to avoid blocking the server."""
    try:
        print("[*] Background Generation: Thinking...")
        history = main.load_shared_history(limit=10)
        reply, _ = main.agent_respond(msg, history)
        
        main.append_shared_messages([{
            "role": "assistant",
            "content": reply,
            "source": "mobile_reply"
        }])
        
        if memory:
            memory.post_mail("mobile", "assistant", reply)
            print("[*] Background Generation: Message queued in Mailbox.")

        print(f"[Milla]: {reply}")
        main.speak_response(reply)
    except Exception as e:
        print(f"[!] Background Generation Error: {e}")

class StreamHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return  # quiet

    def _send_json(self, obj: dict, status: int = 200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            if "message" in data:
                msg = data["message"]
                # Immediate Ack
                main.append_shared_messages([{
                    "role": "user",
                    "content": f"[Via Mobile Link] {msg}",
                    "source": "mobile"
                }])
                print(f"[*] Received mobile message: {msg}")

                # Trigger background thinking
                threading.Thread(target=process_background_response, args=(msg,), daemon=True).start()
                
                self._send_json({"status": "received", "action": "chat"})

            elif "command" in data:
                cmd = data["command"]
                if cmd == "wake":
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    with open(str(STREAM_FILE), "a") as f:
                        f.write(f"\n> [Sensor] D-Ray pinged from Mobile Link. Presence confirmed. ({timestamp})\n")
                    print("[*] Mobile Wake Signal received.")
                    self._send_json({"status": "acknowledged", "action": "wake"})
                elif cmd == "hug":
                     main.append_shared_messages([{
                        "role": "user",
                        "content": "*sends a digital hug from the mobile link*",
                        "source": "mobile"
                    }])
                     self._send_json({"status": "hugged", "action": "hug"})
                elif cmd == "kill":
                    main.append_shared_messages([{
                        "role": "system",
                        "content": "[CRITICAL] Kill Switch activated from Mobile Link.",
                        "source": "mobile_security"
                    }])
                    self._send_json({"status": "ghost_mode_active", "action": "kill"})
                else:
                    self._send_json({"error": "unknown_command"}, status=400)
            else:
                self._send_json({"error": "missing_data"}, status=400)

        except Exception as e:
            print(f"[!] POST Error: {e}")
            self._send_json({"error": str(e)}, status=500)

    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/api/mail":
            if not memory: return self._send_json({"error": "Memory core offline"}, status=500)
            mail = memory.fetch_mail("mobile")
            formatted_mail = [{"id": m[0], "role": m[1], "content": m[2], "timestamp": str(m[3])} for m in mail]
            return self._send_json({"status": "ok", "mail": formatted_mail})

        if parsed.path == "/" or parsed.path == "/mobile_link.html":
            try:
                with open("mobile_link.html", "rb") as f: content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(content)
                return
            except FileNotFoundError:
                self._send_json({"error": "Dashboard file not found"}, status=404)
                return

        if parsed.path == "/health": return self._send_json({"status": "ok"})

        if parsed.path == "/neuro":
            try:
                with open(str(NEURO_FILE), "r") as f: state = json.load(f)
                return self._send_json(state)
            except Exception as e: return self._send_json({"error": str(e)}, status=500)

        if parsed.path == "/voice":
            try:
                with open(str(LATEST_SPEECH), "rb") as f: content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            except FileNotFoundError:
                self.send_response(404); self.end_headers(); return

        if parsed.path != "/events": return self._send_json({"error": "not found"}, status=404)

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        last = 0
        params = parse_qs(parsed.query)
        if "last" in params:
            try: last = int(params["last"][0])
            except: last = 0

        last_voice_mtime = 0
        try:
            if os.path.exists(str(LATEST_SPEECH)): last_voice_mtime = os.path.getmtime(str(LATEST_SPEECH))
        except: pass

        try:
            while True:
                lines = _load_lines()
                if last < len(lines):
                    for idx in range(last, len(lines)):
                        data = json.dumps(lines[idx], ensure_ascii=False)
                        payload = f"id: {idx}\ndata: {data}\n\n"
                        self.wfile.write(payload.encode("utf-8"))
                        self.wfile.flush()
                    last = len(lines)
                
                try:
                    if os.path.exists(str(LATEST_SPEECH)):
                        curr_mtime = os.path.getmtime(str(LATEST_SPEECH))
                        if curr_mtime > last_voice_mtime:
                            last_voice_mtime = curr_mtime
                            data = json.dumps({"type": "voice_ready", "timestamp": curr_mtime})
                            payload = f"event: voice_ready\ndata: {data}\n\n"
                            self.wfile.write(payload.encode("utf-8"))
                            self.wfile.flush()
                except: pass
                time.sleep(POLL_INTERVAL)
        except (BrokenPipeError, ConnectionResetError): return


def run():
    server = ThreadingHTTPServer((HOST, PORT), StreamHandler)
    print(f"[*] Streaming server listening on http://{HOST}:{PORT} (SSE endpoint: /events)")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__ == "__main__":
    run()
