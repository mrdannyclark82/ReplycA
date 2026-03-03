#!/bin/bash

# Get absolute path to the agents
AGENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define paths
SECURITY_AGENT="$AGENT_DIR/security_agent/security_agent.py"
INVESTIGATIVE_AGENT="$AGENT_DIR/investigative_agent/investigative_agent.py"
NETWORK_AGENT="$AGENT_DIR/network_security_agent/network_security_agent.py"

# Create a temporary crontab file
TMP_CRON=$(mktemp)

# Read existing cron
crontab -l > "$TMP_CRON" 2>/dev/null

# Remove existing entries for these agents to avoid duplicates
sed -i '/security_agent.py/d' "$TMP_CRON"
sed -i '/investigative_agent.py/d' "$TMP_CRON"
sed -i '/network_security_agent.py/d' "$TMP_CRON"

# Add new staggered entries (Every 3 hours: 0, 15, 30 minutes past the hour)
echo "0 */3 * * * /usr/bin/python3 $SECURITY_AGENT >> $AGENT_DIR/../security_data/cron.log 2>&1" >> "$TMP_CRON"
echo "15 */3 * * * /usr/bin/python3 $INVESTIGATIVE_AGENT >> $AGENT_DIR/../security_data/cron.log 2>&1" >> "$TMP_CRON"
echo "30 */3 * * * /usr/bin/python3 $NETWORK_AGENT >> $AGENT_DIR/../security_data/cron.log 2>&1" >> "$TMP_CRON"

# Apply the new cron
crontab "$TMP_CRON"
rm "$TMP_CRON"

echo "Security agents have been scheduled on staggered cron cycles (every 3 hours)."
echo "Logs will be written to security_data/cron.log"
