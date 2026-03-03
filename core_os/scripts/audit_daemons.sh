#!/bin/bash

echo "[*] DAEMON WATCH: Auditing active services..."

# List running systemd services (user & system)
systemctl list-units --type=service --state=running --no-pager --plain | head -n 20

echo "---------------------------------------------------"
echo "[*] CHECKING FOR UNKNOWN DAEMONS..."

# Simple heuristic: Check for processes not in a whitelist (Mock)
# In production, this would compare against a known-good list.
# For now, we list user processes that might be "daemons"
ps aux | awk '$8 ~ /^[Ss]/ {print $11}' | sort | uniq -c | sort -nr | head -n 10

echo "---------------------------------------------------"
echo "[*] Rayne OS Specific Daemons:"
ps aux | grep -E "milla|ollama|nexus" | grep -v grep

echo "[*] Daemon Audit Complete."
