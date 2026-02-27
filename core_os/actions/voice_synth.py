import requests
import os
import sys
import tempfile
import re
import subprocess
from dotenv import load_dotenv

# Load .env from root
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

# ElevenLabs Configuration
VOICE_ID = "lfjIPXgW1aWWQrlKK4ww" # Southern Raspy
API_KEY = os.getenv("ELEVENLABS_API_KEY")

def strip_code_blocks(text):
    """Remove code blocks and markdown junk before TTS."""
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)
    text = re.sub(r'[*#_]', '', text) # Remove common markdown
    return text.strip()

def generate_and_play(text):
    if not text: return
    if not API_KEY:
        print("[!] Error: ELEVENLABS_API_KEY missing.")
        return

    # 1. Clean and Prepare
    clean_text = strip_code_blocks(text)
    if not clean_text: return

    # Pronunciation corrections
    clean_text = clean_text.replace("Cadyn", "Kay-Din")
    clean_text = clean_text.replace("D-Ray", "Dee-Ray")
    clean_text = clean_text.replace("Dray", "Dee-Ray")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": clean_text,
        "model_id": "eleven_turbo_v2",
        "voice_settings": {
            "stability": 0.35,
            "similarity_boost": 0.85,
            "style": 0.45,
            "use_speaker_boost": True
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name
            
            # Play using mpv or aplay
            subprocess.run(["mpv", "--no-video", tmp_path], check=False)
            os.remove(tmp_path)
        else:
            print(f"[!] ElevenLabs Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[!] Vocal Synth Error: {e}")

if __name__ == "__main__":
    msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Vocal link active."
    generate_and_play(msg)
