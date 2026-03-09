"""
computer_use.py — Desktop + Browser action toolkit for Milla
Exposes atomic actions: screenshot, click, type, key, scroll, drag,
browser_goto, browser_click, browser_fill, browser_text, shell.
"""
from __future__ import annotations
import base64, os, subprocess, tempfile, time
from typing import Any

import pyautogui

pyautogui.FAILSAFE = True   # move mouse to corner to abort
pyautogui.PAUSE   = 0.08    # small delay between PyAutoGUI calls

# ── Playwright browser singleton ──────────────────────────────────────────────
_pw        = None
_browser   = None
_page      = None
_headless  = os.getenv("BROWSER_HEADLESS", "0") == "1"  # set BROWSER_HEADLESS=1 for silent mode


def set_headless(value: bool):
    global _headless
    _headless = value

def _get_page():
    global _pw, _browser, _page
    if _page is None:
        from playwright.sync_api import sync_playwright
        _pw      = sync_playwright().__enter__()
        _browser = _pw.chromium.launch(headless=_headless, args=["--no-sandbox"])
        _page    = _browser.new_page()
    return _page


def close_browser():
    global _pw, _browser, _page
    if _browser:
        try: _browser.close()
        except: pass
    if _pw:
        try: _pw.__exit__(None, None, None)
        except: pass
    _pw = _browser = _page = None


# ── Screenshot util ───────────────────────────────────────────────────────────
def take_screenshot(scale: float = 0.5) -> str:
    """Return a base64 PNG screenshot, downscaled for vision API efficiency."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    try:
        subprocess.run(
            ["gnome-screenshot", "-f", path],
            timeout=5, check=True,
            env={**os.environ, "DISPLAY": os.getenv("DISPLAY", ":0.0")}
        )
    except Exception:
        # fallback to ImageMagick import
        subprocess.run(["import", "-window", "root", path], timeout=5, check=True,
                       env={**os.environ, "DISPLAY": os.getenv("DISPLAY", ":0.0")})

    # downscale with ImageMagick for smaller payload
    if scale < 1.0:
        scaled = path.replace(".png", "_s.png")
        subprocess.run(
            ["convert", path, "-resize", f"{int(scale*100)}%", scaled],
            timeout=5
        )
        if os.path.exists(scaled):
            os.unlink(path)
            path = scaled

    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    os.unlink(path)
    return b64


# ── Action executor ───────────────────────────────────────────────────────────
def execute_action(action: dict[str, Any]) -> str:
    """
    Execute a single action dict returned by the vision model.
    Returns a short human-readable result string.
    """
    kind = action.get("action", "")
    args = action.get("args", {})

    if kind == "screenshot":
        # just take screenshot — agent loop handles it
        return "screenshot taken"

    elif kind == "click":
        x, y = int(args.get("x", 0)), int(args.get("y", 0))
        button = args.get("button", "left")
        double = args.get("double", False)
        if double:
            pyautogui.doubleClick(x, y, button=button)
        else:
            pyautogui.click(x, y, button=button)
        return f"clicked ({x},{y})"

    elif kind == "type":
        text = args.get("text", "")
        pyautogui.write(text, interval=0.04)
        return f"typed: {text[:40]}"

    elif kind == "key":
        keys = args.get("keys", [])
        if isinstance(keys, str):
            keys = [keys]
        pyautogui.hotkey(*keys)
        return f"key: {'+'.join(keys)}"

    elif kind == "scroll":
        x, y  = int(args.get("x", 0)), int(args.get("y", 0))
        delta = int(args.get("delta", -3))
        pyautogui.scroll(delta, x=x, y=y)
        return f"scrolled {delta} at ({x},{y})"

    elif kind == "drag":
        pyautogui.drag(
            int(args.get("dx", 0)),
            int(args.get("dy", 0)),
            duration=float(args.get("duration", 0.3))
        )
        return "dragged"

    elif kind == "move":
        x, y = int(args.get("x", 0)), int(args.get("y", 0))
        pyautogui.moveTo(x, y, duration=0.2)
        return f"moved to ({x},{y})"

    elif kind == "browser_goto":
        url = args.get("url", "")
        page = _get_page()
        page.goto(url, timeout=15000)
        page.wait_for_load_state("domcontentloaded")
        return f"browser navigated → {url}"

    elif kind == "browser_click":
        sel = args.get("selector", "")
        _get_page().click(sel, timeout=8000)
        return f"browser clicked: {sel}"

    elif kind == "browser_fill":
        sel  = args.get("selector", "")
        text = args.get("text", "")
        _get_page().fill(sel, text, timeout=8000)
        return f"browser filled {sel}: {text[:30]}"

    elif kind == "browser_text":
        sel = args.get("selector", "body")
        txt = _get_page().inner_text(sel)
        return txt[:600]

    elif kind == "browser_screenshot":
        b64 = base64.b64encode(_get_page().screenshot()).decode()
        return b64  # caller will detect this is an image

    elif kind == "shell":
        cmd = args.get("cmd", "")
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=30, env={**os.environ, "DISPLAY": os.getenv("DISPLAY", ":0.0")}
        )
        out = (result.stdout + result.stderr).strip()
        return out[:500] or "(no output)"

    elif kind == "wait":
        secs = float(args.get("seconds", 1.0))
        time.sleep(min(secs, 10))
        return f"waited {secs}s"

    elif kind == "done":
        return f"DONE: {args.get('result', 'task complete')}"

    else:
        return f"unknown action: {kind}"
