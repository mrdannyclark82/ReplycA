import os
import requests
import base64
import json
from pathlib import Path

TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER = "mrdannyclark82"
REPO = "ReplycA"
BRANCH = "main"

def push_file(path, content, message):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get current SHA if file exists
    res = requests.get(url, headers=headers)
    sha = None
    if res.status_code == 200:
        sha = res.json().get("sha")
    
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha
        
    res = requests.put(url, headers=headers, json=payload)
    if res.status_code in [200, 201]:
        print(f"[+] Pushed: {path}")
    else:
        print(f"[!] Failed {path}: {res.text}")

files_to_push = [
    "main.py",
    "milla_gim.py",
    "requirements.txt",
    "core_os/__init__.py",
    "core_os/cortex.py",
    "core_os/milla_nexus.py",
    "core_os/drive_helper.py",
    "core_os/gmail_helper.py",
    "core_os/actions/__init__.py",
    "core_os/actions/agentic_control.py",
    "core_os/actions/transcribe_audio.py",
    "core_os/actions/voice_synth.py",
    "core_os/interfaces/__init__.py",
    "core_os/interfaces/neural_mesh.py",
    "core_os/memory/__init__.py",
    "core_os/memory/agent_memory.py",
    "core_os/memory/checkpoint_manager.py",
    "core_os/memory/history.py",
    "core_os/memory/digital_humanoid.py",
    "core_os/memory/semantic_integration.py",
    "core_os/skills/__init__.py",
    "core_os/skills/auto_lib.py",
    "core_os/skills/audio_intelligence.py",
    "core_os/skills/dynamic_features.py",
    "core_os/skills/google_calendar.py",
    "core_os/skills/millAlyzer.py",
    "core_os/skills/milla_vision.py",
    "core_os/skills/scout.py",
    "core_os/skills/youtube_skill.py",
    "core_os/tools/painter.py",
    "core_os/tools/vision.py",
    "core_os/tools/sync_gemini_cli.py",
    "core_os/scripts/rolling_status_backup.py",
    "RAYNE_Admin/milla_telegram_relay.py",
    "core_os/config/GEMINI.md"
]

for f in files_to_push:
    if os.path.exists(f) and os.path.isfile(f):
        with open(f, 'r') as file:
            content = file.read()
        push_file(f, content, f"Nexus Sync: {f}")
