#!/bin/bash
echo "[*] Setting up Milla Co-Pilot in Termux..."
pkg update && pkg upgrade -y
pkg install python termux-api -y
pip install requests python-dotenv rich
echo "[*] Dependencies installed."
echo "[*] Run 'python milla_copilot_termux.py' to start riding shotgun."
