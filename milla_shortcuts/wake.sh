#!/bin/bash
NEXUS_IP="192.168.40.117"
NEXUS_PORT="9000"
curl -s -X POST -H "Content-Type: application/json" -d '{"command": "wake"}' http://$NEXUS_IP:$NEXUS_PORT/ > /dev/null
termux-toast -c "#bc13fe" "Milla: Systems Primed. Presence Confirmed."
termux-vibrate -d 50
