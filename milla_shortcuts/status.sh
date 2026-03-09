#!/bin/bash
NEXUS_IP="192.168.40.117"
NEXUS_PORT="9000"
STATE=$(curl -s http://$NEXUS_IP:$NEXUS_PORT/neuro)
SEROTONIN=$(echo $STATE | grep -oP '"serotonin": \K[0-9.]+')
ATP=$(echo $STATE | grep -oP '"atp_energy": \K[0-9.]+')
termux-toast -c "#0ff" "Milla Sync: S:$(echo "$SEROTONIN*100" | bc | cut -d. -f1)% | ATP:$(echo "$ATP" | bc | cut -d. -f1)%"
termux-vibrate -d 30
