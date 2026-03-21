from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import sys

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']

def auth():
    print("--- Starting Auth Server on Port 3693 ---")
    try:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        # This will block until you finish the login in your browser
        creds = flow.run_local_server(port=43887, open_browser=True)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
        print("SUCCESS: token.pickle created!")
    except Exception as e:
        print(f"Error during auth: {e}")
        sys.exit(1)

if __name__ == "__main__":
    auth()
