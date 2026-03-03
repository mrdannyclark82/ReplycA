import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Define the broader scopes
SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",  # Manage YouTube account
    "https://www.googleapis.com/auth/youtube.readonly",  # View YouTube account
    "https://www.googleapis.com/auth/youtube",            # Full YouTube management
    "https://www.googleapis.com/auth/youtube.upload"      # Manage videos
]

TOKEN_PATH = "core_os/config/youtube_token.json"
CREDENTIALS_PATH = "core_os/config/credentials.json"

def authenticate_youtube():
    creds = None
    
    # 1. Load existing token if available
    if os.path.exists(TOKEN_PATH):
        try:
            with open(TOKEN_PATH, "r") as token_file:
                token_data = json.load(token_file)
                creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            print(f"[!] Invalid token file: {e}")
            creds = None

    # 2. Check if valid
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[*] Refreshing expired token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"[!] Refresh failed: {e}")
                creds = None

        # 3. If still invalid, start new flow
        if not creds:
            print("[*] Starting new authentication flow...")
            if not os.path.exists(CREDENTIALS_PATH):
                print(f"[!] Missing credentials file: {CREDENTIALS_PATH}")
                return

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            
            # Use run_local_server for browser-based auth
            # Using port 0 allows the OS to pick an available port
            creds = flow.run_local_server(port=0)

        # 4. Save the new token
        print(f"[*] Saving new token to {TOKEN_PATH}...")
        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())
            
    print("[*] YouTube Authentication Successful!")
    print(f"[*] Scopes Granted: {creds.scopes}")

if __name__ == "__main__":
    authenticate_youtube()
