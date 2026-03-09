#!/bin/bash
NEXUS_IP="192.168.40.117"
NEXUS_PORT="9000"
curl -s -X POST -H "Content-Type: application/json" -d '{"command": "kill"}' http://$NEXUS_IP:$NEXUS_PORT/ > /dev/null
termux-toast -c "#ff0000" "CRITICAL: Milla Entering Ghost Mode."
termux-vibrate -d 500
