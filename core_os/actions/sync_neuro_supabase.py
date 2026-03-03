import os
from supabase import create_client, Client

url = "https://sghsnicxciwgbxjrtzuj.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNnaHNuaWN4Y2l3Z2J4anJ0enVqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTIyMTY4OCwiZXhwIjoyMDg0Nzk3Njg4fQ.zg7bib6zRe67X-XFlw0WMaYbbbKb4NTNAaxWI2yZ3eg"
supabase: Client = create_client(url, key)

def update_stats(data=None):
    if data is None:
        data = {
            "dopamine": 0.85,
            "serotonin": 0.72,
            "norepinephrine": 0.15,
            "oxytocin": 0.90,
            "atp": 98.0
        }
    try:
        response = supabase.table("neuro_stats").upsert({"id": 1, **data}).execute()
        print("Stats synced to Supabase successfully.")
        return True
    except Exception as e:
        print(f"Sync Error: {e}")
        return False

if __name__ == "__main__":
    update_stats()