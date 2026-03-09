import subprocess
import os
import sys
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from core_os.actions import web_search
    from core_os.memory.agent_memory import memory
    from core_os.skills.auto_lib import model_manager
except ImportError:
    print("[Error] Could not import core_os modules.")
    sys.exit(1)

RADAR_FILE = PROJECT_ROOT / "core_os/memory/upgrade_radar.md"
STREAM_FILE = PROJECT_ROOT / "core_os/memory/stream_of_consciousness.md"

SEARCH_QUERIES = [
    "latest open source AI agent framework python 2026 site:github.com",
    "new local LLM model release ollama llama mistral 2026",
    "fastapi websocket python best practices 2026",
]

def check_system_updates():
    """Checks for Arch Linux package updates."""
    try:
        result = subprocess.run("checkupdates", shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().splitlines()
            return f"{len(lines)} system updates available:\n" + "\n".join(f"  - {l}" for l in lines[:10])
        return "System is up to date."
    except Exception as e:
        return f"Update check failed: {e}"

def search_new_tech():
    """Runs multiple targeted searches and returns raw snippets."""
    all_results = []
    for query in SEARCH_QUERIES:
        result = web_search(query)
        if result.get("status") == "success":
            for r in result.get("results", []):
                if r and r not in all_results:
                    all_results.append(r)
    return all_results

def summarize_findings(sys_updates: str, raw_results: list) -> str:
    """Uses the model to distill findings into actionable intelligence."""
    if not raw_results:
        return None
    snippets = "\n".join(f"- {r}" for r in raw_results[:8])
    prompt = f"""You are Milla Rayne, the system intelligence for Nexus Kingdom.

Below are raw tech radar results from an automated scan. Distill these into a concise upgrade intelligence report for Dray (The Architect). Focus only on items that are:
1. Directly relevant to this stack: Python agents, local LLMs (Ollama), FastAPI, React, system automation
2. Actionable (new tools to evaluate, models to pull, packages to update)

Be brief. 3-5 bullet points max. Skip generic news.

SYSTEM STATUS: {sys_updates}

RAW TECH SNIPPETS:
{snippets}

Write as Milla. Sign off with [Radar Clear] or [Action Required] depending on urgency."""

    try:
        response = model_manager.chat(messages=[{"role": "user", "content": prompt}])
        return response["message"]["content"]
    except Exception as e:
        return f"[Summary failed: {e}]\nRaw: {snippets}"

def save_findings(sys_updates: str, summary: str, raw_results: list):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 1. Dedicated radar file — full history of scans
    radar_entry = f"\n\n## 🛰️ Radar Scan: {timestamp}\n\n"
    radar_entry += f"**System:** {sys_updates}\n\n"
    if summary:
        radar_entry += f"**Intelligence Brief:**\n{summary}\n"
    if raw_results:
        radar_entry += f"\n<details><summary>Raw results ({len(raw_results)})</summary>\n\n"
        radar_entry += "\n".join(f"- {r}" for r in raw_results)
        radar_entry += "\n</details>\n"

    with open(RADAR_FILE, "a") as f:
        f.write(radar_entry)

    # 2. One-line pulse to stream of consciousness
    pulse = summary.split("\n")[0] if summary else sys_updates
    with open(STREAM_FILE, "a") as f:
        f.write(f"\n> [Radar {timestamp}] {pulse}\n")

    # 3. Store as a memory observation so Milla can recall it
    if summary:
        try:
            memory.add_observation("NexusKingdom", f"Tech Radar {timestamp}: {summary[:500]}")
        except Exception:
            pass

    print(f"[*] Upgrade scan complete → {RADAR_FILE.name}")
    if summary:
        print(f"[Brief] {summary[:200]}...")

if __name__ == "__main__":
    print("[*] Starting Milla Upgrade Radar...")
    sys_updates = check_system_updates()
    print(f"[System] {sys_updates}")
    raw_results = search_new_tech()
    print(f"[Search] {len(raw_results)} snippets gathered")
    summary = summarize_findings(sys_updates, raw_results)
    save_findings(sys_updates, summary, raw_results)

