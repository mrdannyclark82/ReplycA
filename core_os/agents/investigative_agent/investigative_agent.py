import os
import sys
import subprocess
from datetime import datetime

# Shared utils
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import security_utils

DATA_DIR = security_utils.DATA_DIR

def check_logs():
    flags = []
    log_files = [
        "/var/log/syslog",
        "/var/log/auth.log",
        os.path.expanduser("~/.xsession-errors")
    ]
    
    keywords = ["failed password", "authentication failure", "segfault", "error", "critical"]
    
    for log_file in log_files:
        if os.path.exists(log_file) and os.access(log_file, os.R_OK):
            try:
                # Read last 100 lines for efficiency
                proc = subprocess.run(["tail", "-n", "100", log_file], capture_output=True, text=True)
                lines = proc.stdout.splitlines()
                
                for line in lines:
                    for keyword in keywords:
                        if keyword in line.lower():
                            flags.append(f"Suspicious log entry in {log_file}: {line.strip()}")
            except Exception as e:
                pass # Silent fail for restricted files
        else:
            # Try dmesg if available (usually requires sudo but sometimes readable)
            pass

    return flags

def scan_directory(path):
    flags = []
    suspicious_extensions = [".exe", ".bat", ".cmd", ".vbs", ".sh"] # potentially dangerous scripts if out of place
    suspicious_filenames = ["passwords.txt", "secrets.json", "id_rsa", "config.py.bak"] # naive check
    
    # Check if path exists
    if not os.path.exists(path):
        return [f"Directory not found: {path}"]

    try:
        for root, dirs, files in os.walk(path):
            # Skip hidden directories like .git
            if "/." in root:
                continue
                
            for file in files:
                filepath = os.path.join(root, file)
                
                # Check extensions
                _, ext = os.path.splitext(file)
                if ext in suspicious_extensions:
                    # Just a flag, not necessarily malicious
                    flags.append(f"Suspicious file extension in {path}: {filepath}")
                
                # Check filenames
                if file in suspicious_filenames:
                    flags.append(f"Sensitive filename found in {path}: {filepath}")
                    
                # Basic content check (only for small text files)
                try:
                    if os.path.getsize(filepath) < 1024 * 10: # < 10KB
                        with open(filepath, 'r', errors='ignore') as f:
                            content = f.read()
                            if "password =" in content or "API_KEY =" in content:
                                flags.append(f"Potential secret in file in {path}: {filepath}")
                except:
                    pass
    except Exception as e:
        flags.append(f"Error scanning directory {path}: {e}")
        
    return flags

def main():
    print("Running Investigative Agent...")
    flags = check_logs()
    
    # Add directory scanning for RAYNE-Admin
    target_dir = os.path.expanduser("~/RAYNE-Admin")
    dir_flags = scan_directory(target_dir)
    if dir_flags:
        flags.extend(dir_flags)
    
    if flags:
        print(f"Found {len(flags)} concerning entries. Triggering Network Security Agent.")
        for flag in flags:
            security_utils.log_flag("Investigative Agent", flag, level="medium")
            
        # Trigger next agent: Network Security Agent
        next_agent = os.path.join(os.path.dirname(__file__), "../network_security_agent/network_security_agent.py")
        security_utils.trigger_next_agent(next_agent)
    else:
        print("No concerning entries found.")

if __name__ == "__main__":
    main()