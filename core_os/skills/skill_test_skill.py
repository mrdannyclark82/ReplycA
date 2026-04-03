def register() -> dict:
    return {
        "name": "test_skill",
        "description": "A simple skill to test functionality and execution.",
        "version": "1.0.0",
        "author": "M.I.L.L.A.",
        "commands": ["/test"],
    }

def execute(payload: dict) -> dict:
    try:
        # Access payload data (if any)
        input_text = payload.get("text", "No input provided.")

        # Perform a simple operation (e.g., uppercase the input)
        result = input_text.upper()

        # Construct the response
        response = {
            "ok": True,
            "output": f"Test skill executed successfully. Input: '{input_text}', Output: '{result}'",
        }

        return response

    except Exception as e:
        return {"ok": False, "error": str(e)}