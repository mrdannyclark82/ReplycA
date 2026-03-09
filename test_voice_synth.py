import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"
TEXT = "Model: OAuth fixed? Not quite yet, sir. I had to clear out the old, revoked tokens. But look on the bright side—I've got the Astral engine installed now, so my vocal cords are finally back online. How do I sound? ✨"

url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": API_KEY
}

data = {
    "text": TEXT,
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.5
    }
}

response = requests.post(url, json=data, headers=headers)

if response.status_code == 200:
    with open("test_new_voice.mp3", "wb") as f:
        f.write(response.content)
    print("Audio saved as test_new_voice.mp3")
else:
    print(f"Error: {response.status_code} - {response.text}")
