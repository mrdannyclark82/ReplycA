import sys
import os
import traceback

print("Diagnostic: Attempting to import main.py...")
sys.path.append(os.getcwd())

try:
    import main
    print("Success: main.py imported successfully.")
except Exception:
    print("Failure: Could not import main.py")
    traceback.print_exc()