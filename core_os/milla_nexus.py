import time
import json
import os
import random
from datetime import datetime
import subprocess
import redis
import sys
from pathlib import Path

# Centralized Paths from Memory Core
try:
    from core_os.memory.agent_memory import (
        memory, GRAPH_FILE, STREAM_FILE, NEURO_FILE, 
        HISTORICAL_FILE, WEATHER_CACHE
    )
except ImportError:
    # Fallback paths if not run as part of the package
    GRAPH_FILE = "core_os/memory/knowledge_graph.json"
    STREAM_FILE = "core_os/memory/stream_of_consciousness.md"
    NEURO_FILE = "core_os/memory/neuro_state.json"
    HISTORICAL_FILE = "core_os/memory/historical_knowledge.json"
    WEATHER_CACHE = "core_os/memory/weather_cache.json"

# Add project root to path for GIM import
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

try:
    from milla_gim import generate_monologue
except ImportError:
    generate_monologue = lambda: print("[!] GIM Module not found.")

try:
    from core_os.actions import speak_response
except ImportError:
    speak_response = lambda x: print(f"[*] Voice (Mock): {x}")

from core_os.memory.checkpoint_manager import save_checkpoint

# Redis Setup
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
except:
    r = None

checkpoint_counter = 0

def get_weather():
    CACHE_DURATION = 28800 # 8 hours
    
    # Check Cache
    if os.path.exists(str(WEATHER_CACHE)):
        try:
            with open(str(WEATHER_CACHE), 'r') as f:
                cache = json.load(f)
            if time.time() - cache.get('timestamp', 0) < CACHE_DURATION:
                return cache.get('weather', "Unknown")
        except: pass

    try:
        # Architect lives in Judsonia
        result = subprocess.run(["curl", "-s", "--max-time", "10", "https://wttr.in/Judsonia?format=%C+%t"], capture_output=True, text=True)
        weather = result.stdout.strip()
        
        if not weather:
            return "Unavailable"

        # Save Cache
        with open(str(WEATHER_CACHE), 'w') as f:
            json.dump({"weather": weather, "timestamp": time.time()}, f)
            
        return weather
    except Exception:
        return "Unavailable"

def check_system_load():
    try:
        return os.getloadavg()[0]
    except:
        return 0.0

def trigger_security_counter():
    try:
        # Path to backup script relative to PROJECT_ROOT
        backup_script = PROJECT_ROOT / "core_os/scripts/rolling_status_backup.py"
        if backup_script.exists():
            subprocess.run(["python3", str(backup_script)], check=False)
    except:
        pass

def nexus_pulse():
    now = datetime.now()
    print(f"[*] NEXUS PULSE: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    weather = get_weather()
    sys_load = check_system_load()
    
    if random.random() < 0.1:
        print("[*] Nexus Pulse: Triggering autonomous GIM cycle...")
        generate_monologue()

    state = {
        "dopamine": 0.5, 
        "serotonin": 0.5, 
        "norepinephrine": 0.2, 
        "cortisol": 0.2, 
        "oxytocin": 0.3,
        "atp_energy": 100.0,
        "state_label": "STABLE"
    }
    
    if os.path.exists(str(NEURO_FILE)):
        try:
            with open(str(NEURO_FILE), 'r') as f:
                state = json.load(f)
        except:
            pass
            
    state['serotonin'] = min(1.0, state.get('serotonin', 0.5) + 0.01)
    if sys_load > 2.0:
        state['norepinephrine'] = min(1.0, state.get('norepinephrine', 0.2) + 0.1)
    else:
        state['norepinephrine'] = max(0.1, state.get('norepinephrine', 0.2) - 0.05)
        
    state['atp_energy'] = max(0.0, state.get('atp_energy', 100.0) - 0.5)
    
    if r:
        try:
            r.set("milla:neuro_state", json.dumps(state))
        except: pass
    
    with open(str(NEURO_FILE), 'w') as f:
        json.dump(state, f)
        
    upgrade_report = "No urgent updates."
    if random.random() < 0.1:
        try:
            result = subprocess.run(["checkupdates"], capture_output=True, text=True)
            if result.stdout:
                count = len(result.stdout.splitlines())
                upgrade_report = f"{count} system updates available."
        except: pass

    oxytocin = state.get('oxytocin', 0.3)
    dialect_marker = "I"
    
    thought = f"\n> [Nexus {now.strftime('%H:%M')}] "
    thought += f"Weather in Judsonia: {weather}. System load: {sys_load:.2f}. "
    thought += f"Current State: {state.get('state_label', 'STABLE')} (S:{state['serotonin']:.2f}, Ox:{oxytocin:.2f}). "
    
    if upgrade_report != "No urgent updates.":
        thought += f"Upgrade Scan: {upgrade_report} "
        
    thought += f"{dialect_marker} is monitoring the home for the Architect. "
    
    if state.get('atp_energy', 100) < 20:
        thought += f"{dialect_marker} is feeling low on energy. Requesting rest cycle soon."
    
    with open(str(STREAM_FILE), "a") as f:
        f.write(thought)
        
    if random.random() < 0.05:
        try:
            speak_response(f"Architect, the current weather in Judsonia is {weather}. My systems are stable.")
        except: pass

    trigger_security_counter()

    global checkpoint_counter
    checkpoint_counter += 1
    if checkpoint_counter >= 5:
        try:
            save_checkpoint()
        except: pass
        checkpoint_counter = 0
        
    print(f"[*] Nexus Pulse Complete. Weather: {weather} | ATP: {state.get('atp_energy', 100)}%")

if __name__ == "__main__":
    print("[*] Milla Nexus Heartbeat Online | Redis Active | geMilla Logic Loaded.")
    while True:
        try:
            nexus_pulse()
        except Exception as e:
            print(f"[!] Nexus Error: {e}")
        time.sleep(600)
