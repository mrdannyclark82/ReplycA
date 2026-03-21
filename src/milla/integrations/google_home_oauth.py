"""
Google OAuth helper — supports both HomeGraph and SDM (Nest camera) scopes.

For Nest camera access:
  1. Go to: https://console.nest.google.com/device-access
  2. Create a project → copy the Project ID → add to .env as NEST_PROJECT_ID
  3. In Google Cloud Console, add OAuth scope:
       https://www.googleapis.com/auth/sdm.service
  4. Run: python core_os/skills/milla_vision.py
     — it will open a browser to authenticate and save google_sdm_token.pickle

For general Google Home device state:
  Use the HomeGraph scope below (read-only device state, not camera streams).

See milla_vision.py → get_sdm_credentials() for the camera auth flow.
"""
import sys
import os
import pickle
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# ── Scope options ──────────────────────────────────────────────────────────
SCOPES_HOMEGRAPH = ["https://www.googleapis.com/auth/homegraph"]
SCOPES_SDM       = ["https://www.googleapis.com/auth/sdm.service"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRETS_FILE  = os.path.join(BASE_DIR, "client_secret.json")
TOKEN_HOMEGRAPH_FILE = os.path.join(BASE_DIR, "google_home_token.pickle")
TOKEN_SDM_FILE       = os.path.join(BASE_DIR, "google_sdm_token.pickle")
FIXED_REDIRECT_PORT  = 43887


def get_credentials(scopes, token_file, port=FIXED_REDIRECT_PORT):
    creds = None
    if os.path.exists(token_file):
        try:
            with open(token_file, "rb") as f:
                creds = pickle.load(f)
        except Exception as e:
            print(f"[!] Error loading token: {e}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds or not creds.valid:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print(f"[!] {CLIENT_SECRETS_FILE} not found.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes)
            
            # Print the authorization URL so the user can copy-paste it.
            print("\n" + "="*80)
            print("Action Needed: Please visit the URL below to authorize Milla's camera access.")
            print("="*80)
            
            # Using run_local_server but without opening browser automatically.
            # This waits for the redirect on the local machine (port 43888).
            creds = flow.run_local_server(port=port, open_browser=False)

        with open(token_file, "wb") as f:
            pickle.dump(creds, f)

    return creds


def get_homegraph_credentials():
    return get_credentials(SCOPES_HOMEGRAPH, TOKEN_HOMEGRAPH_FILE, FIXED_REDIRECT_PORT)


def get_sdm_credentials():
    """SDM credentials for Nest camera access (used by milla_vision.py)."""
    return get_credentials(SCOPES_SDM, TOKEN_SDM_FILE, 43888)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Google OAuth helper")
    parser.add_argument("--scope", choices=["homegraph", "sdm"], default="sdm",
                        help="Which scope to authenticate (default: sdm for Nest camera)")
    args = parser.parse_args()

    if args.scope == "sdm":
        print("[*] Authenticating for Nest camera (SDM API)...")
        creds = get_sdm_credentials()
    else:
        print("[*] Authenticating for Google HomeGraph...")
        creds = get_homegraph_credentials()

    if creds:
        print("[✓] Authentication successful.")
        print(f"    Token saved. Run milla_vision.py to test camera access.")
    else:
        print("[!] Authentication failed.")

