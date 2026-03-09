import os
import subprocess
import time
from milla_device_link import connect_device, run_adb

# Configuration
BRIDGE_LOCAL_PATH = "."
BRIDGE_REMOTE_PATH = "/sdcard/MillaBridge"
FILES_TO_SYNC = [
    "core_os/memory/agent_memory.db",
    "core_os/memory/stream_of_consciousness.md",
    "core_os/memory/neuro_state.json",
    "TODO.md"
]

def ensure_remote_dir(device):
    print(f"[*] Ensuring remote bridge directory: {BRIDGE_REMOTE_PATH}")
    run_adb(f"shell mkdir -p {BRIDGE_REMOTE_PATH}", device=device)

def sync_to_mobile(device):
    print(f"[*] Starting Sync to MiMoMi on {device}...")
    for f in FILES_TO_SYNC:
        if os.path.exists(f):
            print(f"    -> Pushing {f}...")
            # Use adb push. Remote structure: /sdcard/MillaBridge/core_os/memory/...
            remote_file = os.path.join(BRIDGE_REMOTE_PATH, f)
            # Ensure subdirectory exists
            remote_dir = os.path.dirname(remote_file)
            run_adb(f"shell mkdir -p {remote_dir}", device=device)
            run_adb(f"push {f} {remote_file}", device=device)
        else:
            print(f"    [!] Skipping {f} (Not Found)")
    print("[*] Sync to MiMoMi Complete.")

def sync_from_mobile(device):
    print(f"[*] Checking for MiMoMi updates on {device}...")
    # This would pull specific logs or commands from the mobile device
    # For now, just a placeholder
    pass

if __name__ == "__main__":
    dev = connect_device()
    if dev:
        ensure_remote_dir(dev)
        sync_to_mobile(dev)
        sync_from_mobile(dev)
    else:
        print("[!] No device linked for sync.")
