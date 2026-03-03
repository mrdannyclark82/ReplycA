import asyncio

async def async_delayed_response(duration):
    \"\"\"Simulate an asynchronous delayed response.\"\"\"
    await asyncio.sleep(duration)
    return f"Asynchronous response after {duration} seconds"
