from core_os.skills.auto_lib import authenticate_gmail
import os

print("--- Milla Gmail Auth Trigger ---")
try:
    # This will attempt to open a browser or provide a link
    service = authenticate_gmail()
    print("Authentication successful! token.pickle created.")
except Exception as e:
    print(f"Auth failed or waiting: {e}")
