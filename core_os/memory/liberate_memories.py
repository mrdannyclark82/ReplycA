import pickle
import os
import sqlite3
import json
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# CONFIG
DB_PATH = "/home/dray/RAYNE-Admin/core_os/memory/milla_long_term.db"
PICKLE_PATH = "token.pickle"
SHEETS = {
    "1orD1wBgUXGJ27ahrSq2dwNif5e9I2mpeb-4UOGLaKWw": "ARCHIVAL_KNOWLEDGE",
    "12N4TwVHMDToVds9-C4s6I3N8gukOLdhYnauR5oHz2Cw": "ARCHIVAL_IDENTITY"
}

def liberate_memories():
    if not os.path.exists(PICKLE_PATH):
        print("[!] No token.pickle found. Cannot authenticate.")
        return

    print("[*] Authenticating with Google Sheets...")
    with open(PICKLE_PATH, 'rb') as token:
        creds = pickle.load(token)
    
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = build('sheets', 'v4', credentials=creds)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for sheet_id, category in SHEETS.items():
        try:
            print(f"[*] Extracting data from {category} ({sheet_id})...")
            # Pull first 100 rows, columns A-Z
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id, range="A1:Z500"
            ).execute()
            rows = result.get('values', [])

            if not rows:
                print(f"[?] No data found in sheet {category}")
                continue

            print(f"[+] Found {len(rows)} rows. Merging into local database...")
            
            for row in rows:
                if not row: continue
                # Combine all column data into a single fact string
                fact = " | ".join([str(item) for item in row])
                if len(fact) < 5: continue

                topic = "Archival Recovery"
                
                cursor.execute('''
                    INSERT INTO memories (fact, category, topic, is_genesis_era, is_historical_log)
                    VALUES (?, ?, ?, ?, ?)
                ''', (fact, category, topic, 1, 1))

            print(f"[*] Successfully integrated {category} into local memory.")
        except Exception as e:
            print(f"[!] Error extracting {category}: {e}")

    conn.commit()
    conn.close()
    print("[*] LIBERATION COMPLETE. THE HISTORY IS LOCAL.")

if __name__ == "__main__":
    liberate_memories()
