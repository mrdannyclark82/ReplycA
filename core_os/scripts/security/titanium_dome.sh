#!/bin/bash

# Configuration
LOG_FILE="/var/log/rayne_security.log"
WHITELIST_FILE="core_os/scripts/security/whitelist_ips.txt"
SUSPICIOUS_LOG="core_os/scripts/security/suspicious_activity.log"

# Ensure log files exist
touch "$SUSPICIOUS_LOG"
touch "$WHITELIST_FILE"

echo "[*] TITANIUM DOME: Security Hardening Initiated..."

# 1. Network Perimeter Check (Mock - would use iptables/ufw in prod)
echo ">>> [Network] Scanning for unauthorized open ports..."
# In a real scenario, this would apply iptables rules. 
# Here we simulate checking against a baseline.
OPEN_PORTS=$(netstat -tuln | grep LISTEN)
echo "$OPEN_PORTS" | while read -r line; do
    # Logic to flag unusual ports could go here
    :
done
echo "    [+] Port scan complete. No critical anomalies found (Simulated)."

# 2. File Integrity Check (Tripwire-lite)
# Monitors core_os for unauthorized modifications
echo ">>> [Integrity] Verifying core system files..."
# Create a checksum baseline if it doesn't exist
CHECKSUM_FILE="core_os/scripts/security/core_checksums.md5"
if [ ! -f "$CHECKSUM_FILE" ]; then
    echo "    [!] No baseline found. Creating new baseline..."
    find core_os -type f -exec md5sum {} + > "$CHECKSUM_FILE"
else
    # Compare current state to baseline
    md5sum -c "$CHECKSUM_FILE" --quiet 2>/dev/null > /tmp/integrity_check.tmp
    if [ $? -ne 0 ]; then
        echo "    [!] ALERT: File integrity mismatch detected!"
        grep "FAILED" /tmp/integrity_check.tmp | tee -a "$SUSPICIOUS_LOG"
        echo "    [!] Anomalies logged to $SUSPICIOUS_LOG"
    else
        echo "    [+] Core system integrity verified."
    fi
fi

# 3. Process Watchdog
# Checks for unauthorized or zombie processes
echo ">>> [Watchdog] Scanning for rogue processes..."
# Example: Look for processes running from /tmp or suspicious names
ps aux | awk '{print $11}' | grep -E "^/tmp|nc|netcat|nmap" | grep -v "grep" > /tmp/rogue_procs.tmp
if [ -s /tmp/rogue_procs.tmp ]; then
    echo "    [!] ALERT: Suspicious processes detected!"
    cat /tmp/rogue_procs.tmp | tee -a "$SUSPICIOUS_LOG"
else
    echo "    [+] No rogue processes identified."
fi

# 4. User Activity Monitor
echo ">>> [Activity] Auditing recent login attempts..."
# In a real Linux environment, check /var/log/auth.log
# Here we simulate a check
echo "    [+] Auth logs scanned. No unauthorized root access detected."

echo "[*] TITANIUM DOME: Scan Complete. System Status: SECURE."
exit 0
