import os
import subprocess
import sys
import json
from datetime import datetime

# Shared utils
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import security_utils

DATA_DIR = security_utils.DATA_DIR

def check_connections():
    flags = []
    
    # Check listening ports
    try:
        # Use ss (socket stats) which is usually installed
        proc = subprocess.run(["ss", "-tulpn"], capture_output=True, text=True)
        lines = proc.stdout.splitlines()
        
        # Standard ports/services (whitelist)
        whitelist = ["22", "80", "443", "53", "631", "5353", "11434"] # 11434 for ollama
        
        for line in lines[1:]: # Skip header
            parts = line.split()
            if len(parts) >= 5:
                # Format is complicated, usually local_address:port
                local_addr = parts[4]
                if ":" in local_addr:
                    port = local_addr.split(":")[-1]
                    if port not in whitelist:
                        flags.append(f"Suspicious listening port: {port} (Process: {line.strip()})")
                        
    except FileNotFoundError:
        # Fallback to netstat
        try:
            proc = subprocess.run(["netstat", "-tunapl"], capture_output=True, text=True)
            lines = proc.stdout.splitlines()
            for line in lines[2:]:
                parts = line.split()
                if len(parts) >= 4:
                    local_addr = parts[3]
                    if ":" in local_addr:
                        port = local_addr.split(":")[-1]
                        if port not in whitelist:
                            flags.append(f"Suspicious listening port: {port} (Process: {line.strip()})")
        except:
            pass

    return flags

def main():
    print("Running Network Security Agent...")
    flags = check_connections()
    
    if flags:
        print(f"Found {len(flags)} suspicious network connections. Triggering 360 Agent.")
        for flag in flags:
            security_utils.log_flag("Network Security Agent", flag, level="high")
            
        # Trigger next agent: 360 Agent
        next_agent = os.path.join(os.path.dirname(__file__), "../360_agent/360_agent.py")
        security_utils.trigger_next_agent(next_agent)
    else:
        print("No suspicious network activity found.")

if __name__ == "__main__":
    main()
