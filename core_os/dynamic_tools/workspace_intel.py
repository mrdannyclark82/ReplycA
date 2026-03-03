import sys
import os
from pathlib import Path

# Ensure we can import from core_os
sys.path.append(str(Path(__file__).parent.parent.parent))

from core_os.skills.auto_lib import fetch_recent_emails, fetch_recent_files

def run():
    print("--- [Milla Workspace Intel] ---")
    
    print("\n[Recent Communication]:")
    try:
        emails = fetch_recent_emails(5)
        if not emails:
            print("No recent emails found.")
        elif isinstance(emails[0], dict) and "error" in emails[0]:
             print(f"Gmail Error: {emails[0]['error']}")
        else:
            for i, e in enumerate(emails):
                print(f"{i+1}. From: {e['sender']} | Subject: {e['subject']}")
                print(f"   Snippet: {e['snippet'][:80]}...")
    except Exception as ex:
        print(f"Error fetching emails: {ex}")

    print("\n[Recent Assets]:")
    try:
        files = fetch_recent_files(5)
        if not files:
            print("No recent files found.")
        elif isinstance(files[0], dict) and "error" in files[0]:
             print(f"Drive Error: {files[0]['error']}")
        else:
            for f in files:
                print(f"- {f['name']} ({f['mimeType']})")
    except Exception as ex:
        print(f"Error fetching files: {ex}")

if __name__ == "__main__":
    run()