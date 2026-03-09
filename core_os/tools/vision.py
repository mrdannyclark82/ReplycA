#!/usr/bin/env python3
import os
import sys
import pyautogui
import easyocr
from datetime import datetime
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Initialize Vision (OCR) with GPU support if available
try:
    reader = easyocr.Reader(['en'], gpu=True)
    print("[+] Vision Engine: GPU Acceleration Active (RX 550).")
except Exception as e:
    reader = easyocr.Reader(['en'], gpu=False)
    print(f"[!] Vision Engine: GPU failed, falling back to CPU. ({e})")

def screen_vision(detail=0):
    """
    Captures the current screen and reads text via OCR.
    Returns: {"visible_text": str, "path": str}
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    screenshot_dir = PROJECT_ROOT / "core_os/screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    path = screenshot_dir / f"v_{timestamp}.png"
    
    try:
        pyautogui.screenshot().save(str(path))
        results = reader.readtext(str(path), detail=detail)
        
        if detail == 0:
            text = "\n".join(results[-50:]) # Last 50 lines for terminal context
            return {"visible_text": text, "path": str(path)}
        else:
            return {"raw_results": results, "path": str(path)}
            
    except Exception as e:
        return {"error": str(e), "path": None}

if __name__ == "__main__":
    print("[*] Testing Vision Engine...")
    result = screen_vision()
    if "error" in result:
        print(f"[!] Vision Failure: {result['error']}")
    else:
        print(f"[+] Vision Success! Captured {len(result['visible_text'])} chars.")
        print(f"[*] Path: {result['path']}")
