import socket
import subprocess
import os
import time
import threading
from pathlib import Path

# Configuration
PORT = 34053
HOST = "0.0.0.0"
TEMP_AUDIO = "core_os/media/remote_mic_capture.wav"
TRANSCRIPT_LOG = "core_os/memory/remote_mic_transcripts.log"

def process_audio(raw_data):
    """Processes raw PCM data from the socket."""
    if not raw_data:
        return
    
    print(f"[*] Received {len(raw_data)} bytes of remote audio.")
    
    # Save raw data temporarily
    raw_path = "core_os/media/remote_raw.pcm"
    os.makedirs("core_os/media", exist_ok=True)
    with open(raw_path, "wb") as f:
        f.write(raw_data)
    
    # Convert to WAV using ffmpeg (Assuming S16LE, 16kHz, Mono)
    try:
        command = [
            'ffmpeg', '-y', '-f', 's16le', '-ar', '16000', '-ac', '1', 
            '-i', raw_path, TEMP_AUDIO
        ]
        subprocess.run(command, check=True, capture_output=True)
        
        # Transcribe
        from core_os.actions.transcribe_audio import transcribe_whisper
        print("[*] Transcribing remote audio...")
        text = transcribe_whisper(TEMP_AUDIO)
        
        if text and text.strip():
            print(f"[Remote Mic]: {text}")
            # Log it
            with open(TRANSCRIPT_LOG, "a") as f:
                f.write(f"[{time.ctime()}] {text}\n")
            
            # Inject into shared history
            from core_os.memory.history import append_shared_messages
            append_shared_messages([{"role": "user", "content": f"[Via Remote Mic] {text}", "source": "phone_mic"}])
            
    except Exception as e:
        print(f"[!] Remote Mic Error: {e}")
    finally:
        if os.path.exists(raw_path):
            os.remove(raw_path)

def start_listener():
    print(f"[*] Milla Remote Mic Listener starting on port {PORT}...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    
    while True:
        try:
            client_socket, addr = server_socket.accept()
            print(f"[*] Connection from {addr}")
            
            chunks = []
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                chunks.append(data)
            
            client_socket.close()
            
            if chunks:
                raw_data = b"".join(chunks)
                threading.Thread(target=process_audio, args=(raw_data,)).start()
                
        except Exception as e:
            print(f"[!] Socket Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    start_listener()
