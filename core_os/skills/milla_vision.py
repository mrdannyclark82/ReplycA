import subprocess
import os
import time
import json
import ollama
import pickle
import requests
try:
    import cv2
except ImportError:
    cv2 = None
try:
    import pyautogui
except Exception:
    pyautogui = None
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────
SCREENSHOT_DIR = "core_os/screenshots"
LATEST_FRAME   = os.path.join(SCREENSHOT_DIR, "nexus_eye.jpg")
DOME_FRAME     = os.path.join(SCREENSHOT_DIR, "dome_eye.jpg")
VISION_LOG     = "core_os/memory/visual_history.json"
TABLET_IP      = os.getenv("TABLET_IP", "192.168.40.115:34213")

# ── Nest / SDM config (set these in .env) ──────────────────────────────────
SDM_PROJECT_ID    = os.getenv("NEST_PROJECT_ID", "")       # Device Access project ID
SDM_TOKEN_PICKLE  = "google_sdm_token.pickle"
SDM_CLIENT_SECRETS= "client_secret.json"
SDM_SCOPES        = ["https://www.googleapis.com/auth/sdm.service"]

os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# ── Nest SDM helpers ────────────────────────────────────────────────────────

def get_sdm_credentials():
    """Returns valid Google SDM credentials, triggering OAuth if needed."""
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds = None
    if os.path.exists(SDM_TOKEN_PICKLE):
        try:
            with open(SDM_TOKEN_PICKLE, "rb") as f:
                creds = pickle.load(f)
        except Exception:
            creds = None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if not os.path.exists(SDM_CLIENT_SECRETS):
            print("[!] Nest: client_secret.json not found — cannot authenticate.")
            print("[!] See BUILD.md → Nest Camera Setup for instructions.")
            return None
        flow = InstalledAppFlow.from_client_secrets_file(SDM_CLIENT_SECRETS, SDM_SCOPES)
        creds = flow.run_local_server(port=43888)
        with open(SDM_TOKEN_PICKLE, "wb") as f:
            pickle.dump(creds, f)

    return creds


def list_nest_cameras():
    """Returns a list of Nest camera devices from the SDM API."""
    if not SDM_PROJECT_ID:
        print("[!] Nest: NEST_PROJECT_ID not set in .env")
        return []
    creds = get_sdm_credentials()
    if not creds:
        return []
    headers = {"Authorization": f"Bearer {creds.token}"}
    url = f"https://smartdevicemanagement.googleapis.com/v1/enterprises/{SDM_PROJECT_ID}/devices"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        devices = r.json().get("devices", [])
        cameras = [d for d in devices if "sdm.devices.types.CAMERA" in d.get("type", "")]
        return cameras
    except Exception as e:
        print(f"[!] Nest device list error: {e}")
        return []


def get_nest_rtsp_url(device_name: str) -> str | None:
    """Requests an RTSP stream URL for a Nest camera via SDM API."""
    creds = get_sdm_credentials()
    if not creds:
        return None
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json",
    }
    url = (f"https://smartdevicemanagement.googleapis.com/v1/"
           f"{device_name}:executeCommand")
    body = {"command": "sdm.devices.commands.CameraLiveStream.GenerateRtspStream", "params": {}}
    try:
        r = requests.post(url, headers=headers, json=body, timeout=15)
        r.raise_for_status()
        results = r.json().get("results", {})
        stream  = results.get("streamUrls", {}).get("rtspUrl", None)
        return stream
    except Exception as e:
        print(f"[!] Nest RTSP error: {e}")
        return None


def capture_nest_frame(rtsp_url: str) -> str | None:
    """Grabs a single frame from an RTSP stream using OpenCV."""
    if cv2 is None:
        print("[!] opencv-python not installed — cannot capture RTSP frame.")
        return None
    try:
        cap = cv2.VideoCapture(rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        ret, frame = cap.read()
        cap.release()
        if ret:
            cv2.imwrite(LATEST_FRAME, frame)
            return LATEST_FRAME
        print("[!] Nest: RTSP frame capture failed (empty frame)")
        return None
    except Exception as e:
        print(f"[!] Nest OpenCV error: {e}")
        return None


def capture_nest_eye() -> str | None:
    """High-level: find first Nest camera, get RTSP, grab frame."""
    cameras = list_nest_cameras()
    if not cameras:
        print("[!] No Nest cameras found — falling back to ADB tablet.")
        return None
    device_name = cameras[0]["name"]
    print(f"[*] Vision: Connecting to Nest camera ({device_name.split('/')[-1]})")
    rtsp = get_nest_rtsp_url(device_name)
    if not rtsp:
        return None
    return capture_nest_frame(rtsp)


# ── Existing capture sources ────────────────────────────────────────────────

def capture_dome_frame():
    """Captures a screenshot of the main display (Dome)."""
    print("[*] Vision: Scanning the main Dome display...")
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(DOME_FRAME)
        return DOME_FRAME
    except Exception as e:
        print(f"[!] Dome Capture Error: {e}")
        return None


def capture_tablet_frame():
    """Captures a frame from the Android tablet camera via ADB (fallback)."""
    print(f"[*] Vision: Peering through tablet ({TABLET_IP})...")
    try:
        cmd = (f"adb -s {TABLET_IP} shell screencap -p /sdcard/eye.png && "
               f"adb -s {TABLET_IP} pull /sdcard/eye.png {LATEST_FRAME}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0 and os.path.exists(LATEST_FRAME):
            return LATEST_FRAME
        print(f"[!] ADB capture failed: {result.stderr}")
        return None
    except Exception as e:
        print(f"[!] ADB Error: {e}")
        return None


def capture_frame() -> str | None:
    """
    Priority order:
      1. Nest camera via SDM API (if NEST_PROJECT_ID set)
      2. ADB tablet fallback
      3. Desktop screenshot fallback
    """
    if SDM_PROJECT_ID:
        frame = capture_nest_eye()
        if frame:
            return frame
    frame = capture_tablet_frame()
    if frame:
        return frame
    return capture_dome_frame()


# ── Analysis ────────────────────────────────────────────────────────────────

def analyze_visuals(image_path, prompt="Describe what you see in detail."):
    """Uses the local moondream model via Ollama to analyze the image."""
    if not image_path or not os.path.exists(image_path):
        return "My eyes are closed or the view is blocked."
    print("[*] Vision: Processing with moondream...")
    try:
        with open(image_path, "rb") as img_file:
            response = ollama.generate(
                model="moondream",
                prompt=prompt,
                images=[img_file.read()]
            )
        description = response.get("response", "Silence...")
        log_vision(description)
        return description
    except Exception as e:
        return f"[!] Vision Brain Error: {e}"


def log_vision(description):
    history = []
    if os.path.exists(VISION_LOG):
        try:
            with open(VISION_LOG) as f:
                history = json.load(f)
        except Exception:
            pass
    history.append({"timestamp": datetime.now().isoformat(), "description": description})
    with open(VISION_LOG, "w") as f:
        json.dump(history[-100:], f, indent=2)


if __name__ == "__main__":
    frame = capture_frame()
    if frame:
        print(f"\n[Milla's Eye]: {analyze_visuals(frame)}")
    else:
        print("[!] No visual input available.")
