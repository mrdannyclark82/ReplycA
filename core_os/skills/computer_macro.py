"""
computer_macro.py — Record, save, list, and play back action sequences.
Macros are stored as JSON in core_os/memory/macros/.
"""
from __future__ import annotations
import json, os, time
from pathlib import Path
from typing import Any

MACRO_DIR = Path(__file__).parents[2] / "memory" / "macros"
MACRO_DIR.mkdir(parents=True, exist_ok=True)

# In-memory recording buffer
_recording: list[dict[str, Any]] | None = None
_recording_name: str | None = None


def start_recording(name: str) -> str:
    global _recording, _recording_name
    _recording      = []
    _recording_name = name
    return f"Recording started: {name}"


def record_action(action: dict[str, Any]):
    """Call this after each execute_action() to log it into the active recording."""
    if _recording is not None:
        _recording.append({**action, "_ts": time.time()})


def stop_recording() -> str:
    global _recording, _recording_name
    if _recording is None:
        return "No active recording."
    name = _recording_name or "unnamed"
    save_macro(name, _recording)
    count = len(_recording)
    _recording = None
    _recording_name = None
    return f"Saved macro '{name}' with {count} actions."


def save_macro(name: str, actions: list[dict[str, Any]]):
    path = MACRO_DIR / f"{name}.json"
    with open(path, "w") as f:
        json.dump({"name": name, "actions": actions}, f, indent=2)


def list_macros() -> list[dict]:
    macros = []
    for p in sorted(MACRO_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text())
            macros.append({
                "name":    data.get("name", p.stem),
                "steps":   len(data.get("actions", [])),
                "file":    p.name,
                "size_kb": round(p.stat().st_size / 1024, 1),
            })
        except Exception:
            pass
    return macros


def play_macro(name: str, delay: float = 0.15) -> list[str]:
    """
    Execute a saved macro. Returns list of result strings per action.
    Each action is executed via computer_use.execute_action().
    """
    from core_os.skills.computer_use import execute_action

    path = MACRO_DIR / f"{name}.json"
    if not path.exists():
        return [f"Macro '{name}' not found."]

    data   = json.loads(path.read_text())
    steps  = data.get("actions", [])
    results = []

    for i, action in enumerate(steps):
        clean = {k: v for k, v in action.items() if not k.startswith("_")}
        try:
            result = execute_action(clean)
        except Exception as e:
            result = f"error: {e}"
        results.append(f"[{i+1}/{len(steps)}] {clean.get('action','?')} → {result}")
        time.sleep(delay)

    return results


def delete_macro(name: str) -> str:
    path = MACRO_DIR / f"{name}.json"
    if path.exists():
        path.unlink()
        return f"Deleted macro '{name}'."
    return f"Macro '{name}' not found."


def is_recording() -> bool:
    return _recording is not None


def recording_status() -> dict:
    return {
        "recording":      _recording is not None,
        "name":           _recording_name,
        "steps_so_far":   len(_recording) if _recording else 0,
    }
