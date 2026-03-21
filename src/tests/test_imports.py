import sys
import os

print("--- Starting import test ---")

try:
    import requests
    print("requests imported successfully.")
except ImportError as e:
    print(f"ImportError: requests - {e}")

try:
    import json
    print("json imported successfully.")
except ImportError as e:
    print(f"ImportError: json - {e}")

try:
    import time
    print("time imported successfully.")
except ImportError as e:
    print(f"ImportError: time - {e}")

try:
    from datetime import datetime
    print("datetime imported successfully.")
except ImportError as e:
    print(f"ImportError: datetime - {e}")

try:
    import logging
    print("logging imported successfully.")
except ImportError as e:
    print(f"ImportError: logging - {e}")

try:
    from dotenv import load_dotenv
    print("dotenv imported successfully.")
except ImportError as e:
    print(f"ImportError: dotenv - {e}")

# Simulate PROJECT_ROOT calculation
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
# Append ogdray root for core_os imports
sys.path.append(os.path.join(PROJECT_ROOT, "ogdray"))

print(f"Simulated PROJECT_ROOT: {PROJECT_ROOT}")
print(f"sys.path now includes: {sys.path}")


try:
    from core_os.memory.history import load_shared_history, append_shared_messages
    print("core_os.memory.history imported successfully.")
except ImportError as e:
    print(f"ImportError: core_os.memory.history - {e}")

try:
    import nexus_aio
    print("nexus_aio imported successfully.")
except ImportError as e:
    print(f"ImportError: nexus_aio - {e}")

try:
    from core_os.actions import local_llm_process
    print("core_os.actions.local_llm_process imported successfully.")
except ImportError as e:
    print(f"ImportError: core_os.actions.local_llm_process - {e}")

print("--- Import test finished ---")
