import os
import pickle
import json
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar"
]

def authenticate_manual():
    """Manual authentication flow for CLI."""
    # Try to find credentials
    cred_file = "credentials.json"
    if not os.path.exists(cred_file):
        cred_file = "core_os/config/credentials.json"
    if not os.path.exists(cred_file):
        cred_file = "client_secret.json"
    
    if not os.path.exists(cred_file):
        print("Error: No credentials file found.")
        return

    # Use the 'web' configuration but perform a manual code exchange
    # Since it's a 'web' client, we must use one of its registered redirect URIs.
    # The user has: http://localhost:5000/oauth/callback
    redirect_uri = "http://localhost:5000/oauth/callback"

    flow = Flow.from_client_secrets_file(
        cred_file,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

    print("\n--- Milla Manual Auth (Gmail + Calendar) ---")
    print(f"1. Open this URL in your browser:\n\n{auth_url}\n")
    print("2. After you authorize, you'll be redirected to a localhost URL that probably fails.")
    print("3. COPY the 'code' parameter from that URL (the part after ?code= and before &state=).")
    
    auth_code = input("\nPaste the authorization code here: ").strip()

    if auth_code:
        try:
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            
            # Save to both locations
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)
                
            calendar_token_path = "core_os/config/calendar_token.json"
            os.makedirs(os.path.dirname(calendar_token_path), exist_ok=True)
            with open(calendar_token_path, "w") as token:
                token.write(creds.to_json())
                
            print("\nAuthentication successful! All tokens updated.")
            return creds
        except Exception as e:
            print(f"\nAuthentication failed: {e}")
    else:
        print("\nNo code provided. Auth cancelled.")

if __name__ == "__main__":
    authenticate_manual()
