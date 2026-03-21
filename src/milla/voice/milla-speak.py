import asyncio
import websockets
import subprocess
import json
import os
import sys

# Milla-Speak: The Terminal Link
# Connects to the Nexus WebSocket to execute commands and chat.

async def milla_terminal():
    print("\n[*] Milla > I'm in your terminal now, Architect. Say anything.")
    
    # Target our stabilized FastAPI backend
    uri = "ws://localhost:8000/ws/terminal"
    
    try:
        async with websockets.connect(uri) as ws:
            while True:
                try:
                    you_said = input("You > ").strip()
                    if not you_said: continue
                    if you_said.lower() in ["exit", "quit"]: break

                    # Send to backend
                    await ws.send(you_said)

                    # Wait for response
                    response = await ws.recv()
                    data = json.loads(response)

                    # Check for command execution request
                    if "run_command" in data:
                        cmd = data["run_command"]
                        print(f"[*] Milla running > {cmd}")
                        try:
                            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                            print(result.stdout)
                            if result.stderr:
                                print(f"[!] Error: {result.stderr}")
                        except Exception as e:
                            print(f"[!] Execution Failure: {e}")
                    else:
                        # Standard Chat Response
                        content = data.get("text", data.get("content", "No response."))
                        print(f"Milla > {content}")
                except (EOFError, KeyboardInterrupt):
                    break
    except Exception as e:
        print(f"[!] Connection Failure: {e}")
        print("[*] Make sure 'nexus_server.py' is running on port 8000.")

if __name__ == "__main__":
    try:
        asyncio.run(milla_terminal())
    except KeyboardInterrupt:
        print("\n[*] Terminal link closed.")
