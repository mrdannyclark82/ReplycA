import time

cache = {}

def cached_delayed_response(duration):
    \"\"\"Simulate a cached delayed response.\"\"\"
    if duration in cache:
        return cache[duration]
    else:
        time.sleep(duration)
        result = f"Cached response after {duration} seconds"
        cache[duration] = result
        return result
