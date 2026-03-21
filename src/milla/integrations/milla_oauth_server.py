"""
Milla OAuth Server
Handles Google OAuth2.0 flow for the Milla PWA.
Runs on http://0.0.0.0:5000
Callback: http://192.168.40.117:5000/oauth/callback
"""

import os
import pickle
import json
from flask import Flask, redirect, request, jsonify, session
from flask_cors import CORS
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True, origins=["http://192.168.40.117:5173", "http://localhost:5173"])

CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(__file__), "client_secret.json")
TOKEN_PICKLE = os.path.join(os.path.dirname(__file__), "token.pickle")
REDIRECT_URI = "http://localhost:5000/oauth/callback"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/drive.file",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def load_credentials():
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, "rb") as f:
            return pickle.load(f)
    return None


def save_credentials(creds):
    with open(TOKEN_PICKLE, "wb") as f:
        pickle.dump(creds, f)


@app.route("/oauth/login")
def oauth_login():
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, state = flow.authorization_url(access_type="offline", prompt="consent", include_granted_scopes="true")
    session["oauth_state"] = state
    return redirect(auth_url)


@app.route("/oauth/callback")
def oauth_callback():
    state = session.get("oauth_state")
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI, state=state)
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    save_credentials(creds)
    return redirect("http://192.168.40.117:5173/?auth=success")


@app.route("/oauth/status")
def oauth_status():
    creds = load_credentials()
    if not creds:
        return jsonify({"authenticated": False})
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            save_credentials(creds)
        except Exception:
            return jsonify({"authenticated": False})
    if creds.valid:
        return jsonify({"authenticated": True, "email": getattr(creds, "id_token", {}).get("email", "unknown")})
    return jsonify({"authenticated": False})


@app.route("/oauth/logout")
def oauth_logout():
    if os.path.exists(TOKEN_PICKLE):
        os.remove(TOKEN_PICKLE)
    return jsonify({"status": "logged out"})


if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Allow HTTP on LAN
    print("Milla OAuth Server running at http://192.168.40.117:5000")
    print(f"Callback URI: {REDIRECT_URI}")
    print("Register this callback in Google Cloud Console if not done already.")
    app.run(host="0.0.0.0", port=5000, debug=False)
