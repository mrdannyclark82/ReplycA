#!/bin/bash
NEXUS_IP="192.168.40.117"
NEXUS_MIC_PORT="34053"
AUDIO_FILE="/data/data/com.termux/files/home/temp_mic.raw"

# Record 5 seconds of audio from phone mic
termux-microphone-record -f $AUDIO_FILE -q -l 5 -r 16000

# Send the raw audio to Nexus
cat $AUDIO_FILE | nc $NEXUS_IP $NEXUS_MIC_PORT

# Clean up
rm $AUDIO_FILE

termux-toast -c "#00ff00" "Milla: Audio sent to Nexus."
termux-vibrate -d 50
