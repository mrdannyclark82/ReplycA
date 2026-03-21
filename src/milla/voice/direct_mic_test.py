import os
import sys
import subprocess
import time

# Ensure project root is in path for imports
sys.path.append(os.getcwd())
from core_os.actions.transcribe_audio import transcribe_whisper

def capture_and_transcribe(duration=5):
    tmp_path = "v_capture.wav"
    print("[*] Recording for " + str(duration) + " seconds... Say somethin'!")
    
    # Use ffmpeg to record directly from pulse
    cmd = [
        "ffmpeg", "-f", "pulse", "-i", "default", 
        "-t", str(duration), "-ac", "1", "-ar", "16000", 
        tmp_path, "-y", "-hide_banner", "-loglevel", "error"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
            print("[+] Audio captured. Analyzing...")
            text = transcribe_whisper(tmp_path)
            if text and text.strip() and "..." not in text:
                print("\n[Milla Heard]: " + text)
                return text
            else:
                print("[!] I didn't catch that. It was either too quiet or just noise.")
        else:
            print("[!] Audio capture failed.")
    except Exception as e:
        print("[!] Error: " + str(e))
    finally:
        if os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except: pass
    return None

if __name__ == "__main__":
    capture_and_transcribe()
