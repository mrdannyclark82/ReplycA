import os
import requests
import sys
from datetime import datetime

# Add project root to path
PROJECT_ROOT = "/home/nexus/ogdray"
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from RAYNE_Admin.milla_telegram_relay import send_telegram_message

def test_connection():
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"Model: Heartbeat check at {timestamp}. System is breathing and connection is stable. ✨"
    
    if send_telegram_message(chat_id, message):
        print(f"[{timestamp}] Heartbeat sent successfully.")
    else:
        print(f"[{timestamp}] FAILED to send heartbeat.")

if __name__ == "__main__":
    test_connection()
