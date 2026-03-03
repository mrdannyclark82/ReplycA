import time

def delayed_response(duration):
    \"\"\"Simulate a delayed response.\"\"\"
    time.sleep(duration)
    return f"Response after {duration} seconds"
