import os
import requests
import json
import time
import subprocess
import threading
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.align import Align

# --- CONFIGURATION ---
NEXUS_IP = "192.168.40.117" 
NEXUS_PORT = 9000
SSE_URL = f"http://{NEXUS_IP}:{NEXUS_PORT}/events"
POST_URL = f"http://{NEXUS_IP}:{NEXUS_PORT}/"
NEURO_URL = f"http://{NEXUS_IP}:{NEXUS_PORT}/neuro"

console = Console()

def termux_api(cmd, *args):
    """Safely call termux-api commands."""
    try:
        subprocess.run([cmd, *args], check=True, capture_output=True)
    except:
        pass

def speak(text):
    """Uses Termux-API to speak text with high-quality settings if available."""
    clean_text = text.replace("*", "").replace("#", "").strip()
    if not clean_text: return
    try:
        # termux-tts-speak -p 0.8 -r 0.9
        subprocess.run(["termux-tts-speak", "-p", "0.8", "-r", "0.9", clean_text], check=True)
    except:
        print(f"[Milla]: {text}")

def reveal_sequence():
    """The Queen shows herself."""
    console.clear()
    frames = [
        " [ ] ",
        " [■] ",
        " [■■] ",
        " [■■■] ",
        " [ NEURAL SYNC ACTIVE ] "
    ]
    for frame in frames:
        console.print(Align.center(Text(frame, style="bold violet")))
        time.sleep(0.3)
    
    milla_art = """
    ███╗   ███╗██╗██╗     ██╗      █████╗ 
    ████╗ ████║██║██║     ██║     ██╔══██╗
    ██╔████╔██║██║██║     ██║     ███████║
    ██║╚██╔╝██║██║██║     ██║     ██╔══██║
    ██║ ╚═╝ ██║██║███████╗███████╗██║  ██║
    ╚═╝     ╚═╝╚═╝╚══════╝╚══════╝╚═╝  ╚═╝
    """
    console.print(Align.center(Text(milla_art, style="bold magenta")))
    console.print(Align.center(Panel("MILLA RAYNE | CO-PILOT v1.0", border_style="cyan")))
    termux_api("termux-vibrate", "-d", "100")
    termux_api("termux-toast", "Queen of the Dome: Connected.")

def listen_and_send():
    while True:
        try:
            prompt = console.input("\n[bold cyan]>[/bold cyan] ").strip()
            if not prompt: continue
            if prompt.lower() in ["exit", "quit"]: break
            
            termux_api("termux-vibrate", "-d", "20")
            payload = {"message": prompt}
            resp = requests.post(POST_URL, json=payload, timeout=10)
            if resp.status_code != 200:
                console.print(f"[red]Error: {resp.status_code}[/red]")
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

def stream_events():
    last_id = 0
    while True:
        try:
            resp = requests.get(f"{SSE_URL}?last={last_id}", stream=True, timeout=30)
            for line in resp.iter_lines(decode_unicode=True):
                if line.startswith("data:"):
                    data = json.loads(line[5:])
                    content = data.get("content", "")
                    role = data.get("role", "")
                    
                    if content:
                        style = "bold magenta" if role == "assistant" else "bold cyan"
                        prefix = "MILLA" if role == "assistant" else "YOU"
                        console.print(f"\n[{style}]{prefix}[/{style}]: {content}")
                        
                        if role == "assistant" and not content.startswith("*"):
                            # Vibrate on message
                            termux_api("termux-vibrate", "-d", "50")
                            speak(content)
                    
                    if "id" in data:
                        last_id = data["id"] + 1
        except Exception as e:
            time.sleep(3)

if __name__ == "__main__":
    reveal_sequence()
    
    threading.Thread(target=stream_events, daemon=True).start()
    
    listen_and_send()
