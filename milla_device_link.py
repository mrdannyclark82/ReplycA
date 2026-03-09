import subprocess
import os
import re
import time
import json
from datetime import datetime

# Load Environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except: pass

# Replace with your actual phone IP if known, or let discovery try
PHONE_IP = os.getenv("MY_PHONE_IP", "192.168.40.182")
PHONE_TAILSCALE_IP = os.getenv("MY_PHONE_TAILSCALE_IP", "100.113.104.89")

def get_adb_device():
    """Dynamically resolve the active ADB device (Tailscale preferred, then local Wi-Fi)."""
    try:
        result = subprocess.run("adb devices", shell=True, capture_output=True, text=True, timeout=5)
        lines = result.stdout.strip().splitlines()
        tailscale_dev = None
        local_dev = None
        for line in lines[1:]:
            if "\tdevice" not in line:
                continue
            serial = line.split("\t")[0]
            if serial.startswith("100."):
                tailscale_dev = serial
            elif PHONE_IP in serial or PHONE_TAILSCALE_IP in serial:
                local_dev = serial
        return tailscale_dev or local_dev
    except Exception:
        return None

def run_adb(cmd, device=None):
    try:
        prefix = f"adb -s {device}" if device else "adb"
        result = subprocess.run(f"{prefix} {cmd}", shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def connect_device():
    print("[*] Checking ADB status...")
    dev = get_adb_device()
    if dev:
        print(f"[*] Device already connected: {dev}")
        return dev

    # Try local Wi-Fi connect (ADB tcpip mode, port 5555)
    print(f"[*] No device found. Attempting to connect to {PHONE_IP}:5555...")
    result = subprocess.run(f"adb connect {PHONE_IP}:5555", shell=True, capture_output=True, text=True, timeout=10)
    time.sleep(2)
    dev = get_adb_device()
    if dev:
        print(f"[*] Successfully connected: {dev}")
        return dev

    print("[!] Connection failed.")
    return None

def get_stats(dev):
    # 1. Battery
    bat_out = run_adb("shell dumpsys battery", device=dev)
    level = re.search(r"level: (\d+)", bat_out)
    
    # 2. Screen
    pwr_out = run_adb("shell dumpsys power", device=dev)
    screen = re.search(r"mWakefulness=(\w+)", pwr_out)
    
    # 3. Last Activity (What's on screen?)
    activity_out = run_adb("shell dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'", device=dev)
    
    return {
        "battery": level.group(1) if level else "??",
        "screen": screen.group(1) if screen else "unknown",
        "activity": activity_out.strip()[:100] if activity_out else "idle",
        "device": dev
    }

def log_to_milla(stats):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] Device Link [{stats['device']}]: {stats['battery']}% | {stats['screen']} | {stats['activity']}\n"
    
    # Save to device log
    os.makedirs("core_os/memory", exist_ok=True)
    with open("core_os/memory/device_status.log", "a") as f:
        f.write(log_entry)
    
    # Push to Milla's stream if significant (e.g., screen turned on)
    if stats['screen'] == "Awake":
        with open("core_os/memory/stream_of_consciousness.md", "a") as f:
            f.write(f"\n> [Sensor] D-Ray's device just woke up. Presence detected. ({timestamp})\n")

if __name__ == "__main__":
    dev = connect_device()
    if dev:
        stats = get_stats(dev)
        log_to_milla(stats)
        print(f"[*] Milla is now aware of your device state: {stats}")
    else:
        print("[!] Could not link to device. Ensure Wi-Fi Debugging is active on your phone.")
