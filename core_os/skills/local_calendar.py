import json
import os
import datetime

SCHEDULE_FILE = "core_os/memory/local_schedule.json"

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    return []

def save_schedule(events):
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump(events, f, indent=2)

def add_event(summary, start_time, end_time=None):
    """Adds a local event. time format: YYYY-MM-DD HH:MM"""
    events = load_schedule()
    events.append({
        "summary": summary,
        "start": start_time,
        "end": end_time,
        "created_at": datetime.datetime.now().isoformat()
    })
    save_schedule(events)
    return f"Event '{summary}' added to local schedule."

def fetch_local_events(days=7):
    events = load_schedule()
    now = datetime.datetime.now()
    end_date = now + datetime.timedelta(days=days)
    
    upcoming = []
    for e in events:
        try:
            # Parse start time (assuming YYYY-MM-DD format or ISO)
            event_date = datetime.datetime.fromisoformat(e['start'].split('T')[0])
            if now.date() <= event_date.date() <= end_date.date():
                upcoming.append(e)
        except:
            continue
            
    return sorted(upcoming, key=lambda x: x['start'])

def import_from_google(google_events):
    """Merges Google events into local storage."""
    local_events = load_schedule()
    count = 0
    for ge in google_events:
        # Check for duplicates
        if not any(le['summary'] == ge['summary'] and le['start'] == ge['start'] for le in local_events):
            local_events.append({
                "summary": ge['summary'],
                "start": ge['start'],
                "source": "google_import"
            })
            count += 1
    save_schedule(local_events)
    return f"Imported {count} events from Google."

if __name__ == "__main__":
    # Test
    print(fetch_local_events())
