#!/usr/bin/env python3
"""
milla_auto_cron.py — Scheduled runner for milla_auto.py
- Runs milla_auto.py and captures output
- POSTs result to Milla Agent Server (/chat)
- Sends summary to Telegram for Danny's approval
- Auto-detects and persists TELEGRAM_CHAT_ID on first run
"""
import os
import sys
import json
import subprocess
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path("/home/nexus/ogdray")
ENV_FILE = ROOT / ".env"
LOCK_FILE = Path("/tmp/milla_auto_cron.lock")
LOG_FILE = ROOT / "milla_auto_cron.log"
AGENT_SERVER = "http://localhost:7788"

load_dotenv(ENV_FILE, override=False)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)  # cron >> redirect captures this — no extra file write needed


CHAT_ID_FILE = ROOT / "core_os/memory/telegram_chat_id.txt"


def get_or_detect_chat_id() -> str | None:
    """Return saved TELEGRAM_CHAT_ID from env, relay-persisted file, or auto-detect."""
    # 1. Env var (manually set)
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if chat_id:
        return chat_id

    # 2. File written by milla_telegram_relay on last interaction
    if CHAT_ID_FILE.exists():
        chat_id = CHAT_ID_FILE.read_text().strip()
        if chat_id:
            log(f"Loaded chat_id from relay file: {chat_id}")
            return chat_id

    log("ERROR: Could not determine TELEGRAM_CHAT_ID. Send a message to @Mikcobot first.")
    return None


def send_telegram(chat_id: str, text: str, reply_markup: dict | None = None) -> bool:
    """Send a Telegram message, with optional inline keyboard."""
    if not BOT_TOKEN:
        log("ERROR: TELEGRAM_BOT_TOKEN not set.")
        return False
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=10)
        return r.json().get("ok", False)
    except Exception as e:
        log(f"Telegram send failed: {e}")
        return False


def push_to_agent_server(output: str) -> str:
    """POST milla_auto output to the agent server /chat endpoint."""
    try:
        r = requests.post(
            f"{AGENT_SERVER}/chat",
            json={"message": f"[AUTO_CYCLE_REPORT]\n{output}"},
            timeout=30,
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("response", data.get("reply", ""))
    except Exception as e:
        log(f"Agent server push failed: {e}")
    return ""


def run_milla_auto() -> str:
    """Run milla_auto.py and return its stdout output."""
    script = ROOT / "src/milla/milla_auto.py"
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(ROOT),
        )
        out = (result.stdout + result.stderr).strip()
        return out or "(no output)"
    except subprocess.TimeoutExpired:
        return "ERROR: milla_auto.py timed out after 300s"
    except Exception as e:
        return f"ERROR: {e}"


def format_telegram_message(auto_output: str, milla_response: str) -> str:
    """Build the Telegram approval message."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"🤖 *Milla Auto Cycle* — `{ts}`",
        "",
        "*Cycle Output:*",
        f"```\n{auto_output[:800]}{'...' if len(auto_output) > 800 else ''}\n```",
    ]
    if milla_response:
        lines += [
            "",
            "*Milla's Assessment:*",
            f"_{milla_response[:500]}{'...' if len(milla_response) > 500 else ''}_",
        ]
    lines += ["", "Approve this cycle log? ✅ or flag it ⚠️"]
    return "\n".join(lines)


def main():
    # Prevent overlapping runs
    if LOCK_FILE.exists():
        log("Another instance is running (lock file exists). Skipping.")
        return
    LOCK_FILE.touch()

    try:
        log("=== milla_auto_cron: starting cycle ===")

        chat_id = get_or_detect_chat_id()
        if not chat_id:
            return

        # 1. Run milla_auto.py
        log("Running milla_auto.py...")
        auto_output = run_milla_auto()
        log(f"milla_auto output ({len(auto_output)} chars): {auto_output[:200]}...")

        # 2. Push to agent server
        log("Pushing to agent server...")
        milla_response = push_to_agent_server(auto_output)
        if milla_response:
            log(f"Agent server response: {milla_response[:200]}...")

        # 3. Send Telegram approval message
        msg = format_telegram_message(auto_output, milla_response)
        approval_keyboard = {
            "inline_keyboard": [[
                {"text": "✅ Approved", "callback_data": "auto_approve"},
                {"text": "⚠️ Flag for Review", "callback_data": "auto_flag"},
            ]]
        }
        sent = send_telegram(chat_id, msg, reply_markup=approval_keyboard)
        log(f"Telegram message sent: {sent}")
        log("=== milla_auto_cron: cycle complete ===")

    finally:
        LOCK_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
