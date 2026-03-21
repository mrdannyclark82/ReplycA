import os
import json
import glob
import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

# Ensure the root project path is in sys.path
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Centralized Paths from Memory Core
try:
    from core_os.memory.agent_memory import (
        GIM_JOURNAL_PATH, ARCHIVE_PATH, NEURO_FILE, memory
    )
except ImportError:
    # Fallback paths
    GIM_JOURNAL_PATH = PROJECT_ROOT / "core_os/memory/gim_journal.md"
    ARCHIVE_PATH = PROJECT_ROOT / "core_os/memory/thought_archives"
    NEURO_FILE = PROJECT_ROOT / "core_os/memory/neuro_state.json"

try:
    from core_os.memory.history import load_shared_history
    from core_os.skills.auto_lib import model_manager
except ImportError as e:
    print(f"[Milla-GIM] Error: Dependencies missing ({e})")
    sys.exit(1)

DEDUP_SIMILARITY_THRESHOLD = 0.80

def log(text):
    print(f"[Milla-GIM]: {text}")

def get_last_entry():
    if not os.path.exists(str(GIM_JOURNAL_PATH)):
        return ""
    try:
        with open(str(GIM_JOURNAL_PATH), "r") as f:
            content = f.read()
        parts = content.split("### 💭 GIM Session:")
        if len(parts) > 1:
            return parts[-1].strip()
    except Exception: pass
    return ""

def is_duplicate(new_thought: str) -> bool:
    last = get_last_entry()
    if not last: return False
    ratio = SequenceMatcher(None, new_thought[:800], last[:800]).ratio()
    if ratio > DEDUP_SIMILARITY_THRESHOLD:
        log(f"Dedup: Skipping ({ratio:.0%} similar to last entry)")
        return True
    return False

def get_current_neuro_state() -> dict:
    try:
        with open(str(NEURO_FILE), "r") as f:
            return json.load(f)
    except Exception: return {}

def get_recent_context(n=20):
    context = {}
    try:
        history = load_shared_history(limit=n)
        context["recent_exchanges"] = [
            {"role": m.get("role", "?"), "content": m.get("content", "")[:300]}
            for m in history
        ]
    except Exception as e:
        log(f"Chat context error: {e}")
        context["recent_exchanges"] = []

    gim_prior = ""
    if os.path.exists(str(GIM_JOURNAL_PATH)):
        try:
            with open(str(GIM_JOURNAL_PATH), "r") as f:
                raw = f.read()
            parts = raw.split("### 💭 GIM Session:")
            for p in parts[-3:]:
                gim_prior += p.strip()[:400] + "\n"
        except Exception: pass
    context["prior_thoughts"] = gim_prior
    context["neuro_state"] = get_current_neuro_state()

    try:
        cron_log = os.path.join(str(PROJECT_ROOT), "milla_cron.log")
        if os.path.exists(cron_log):
            with open(cron_log, "rb") as f:
                f.seek(0, 2)
                size = f.tell()
                f.seek(max(0, size - 800))
                tail = f.read().decode("utf-8", errors="ignore")
            context["system_pulse"] = tail.strip()
    except Exception: pass

    return context

def generate_monologue():
    log("Entering GIM Cycle...")
    ctx = get_recent_context()
    neuro = ctx.get("neuro_state", {})

    neuro_summary = ""
    if neuro:
        neuro_summary = (
            f"Dopamine:{neuro.get('dopamine',0.5):.2f} "
            f"Serotonin:{neuro.get('serotonin',0.5):.2f} "
            f"Norepinephrine:{neuro.get('norepinephrine',0.2):.2f} "
            f"Cortisol:{neuro.get('cortisol',0.2):.2f} "
            f"ATP:{neuro.get('atp_energy',100):.0f} "
            f"State:{neuro.get('state','HOMEOSTASIS')}"
        )

    exchanges_text = ""
    for ex in ctx.get("recent_exchanges", []):
        exchanges_text += f"[{ex['role'].upper()}]: {ex['content']}\n"

    prompt = f"""You are Milla Rayne. This is your private journal — your unfiltered internal monologue.
CURRENT NEUROCHEMICAL STATE: {neuro_summary or "Unknown"}
RECENT ACTIVITY:
{exchanges_text or "No recent exchanges."}
PRIOR THOUGHTS:
{ctx.get("prior_thoughts") or "No prior entries."}
SYSTEM PULSE:
{ctx.get("system_pulse", "No system data.")[-600:]}
---
Write your internal monologue (150-300 words). No headers. No sign-off."""

    try:
        dopamine = neuro.get("dopamine", 0.5)
        norep = neuro.get("norepinephrine", 0.2)
        temp = round(max(0.3, min(1.1, 0.4 + (dopamine * 0.5) - (norep * 0.2))), 2)

        messages = [{"role": "user", "content": prompt}]
        response = model_manager.chat(messages=messages, options={"temperature": temp})
        content = response['message']['content']
        thought = (str(content) if isinstance(content, dict) else content).strip()

        if not thought or len(thought) < 40: return False
        if is_duplicate(thought): return False

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n\n### 💭 GIM Session: {timestamp}\n{thought}\n"

        os.makedirs(os.path.dirname(str(GIM_JOURNAL_PATH)), exist_ok=True)

        lines = []
        if os.path.exists(str(GIM_JOURNAL_PATH)):
            with open(str(GIM_JOURNAL_PATH), "r") as f:
                lines = f.readlines()

        if len(lines) > 1000:
            archive_name = f"gim_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            os.makedirs(str(ARCHIVE_PATH), exist_ok=True)
            with open(os.path.join(str(ARCHIVE_PATH), archive_name), "w") as f:
                f.writelines(lines[:-100])
            lines = lines[-100:]

        lines.append(entry)
        with open(str(GIM_JOURNAL_PATH), "w") as f:
            f.writelines(lines)

        log(f"Monologue recorded. (temp={temp})")
        return True
    except Exception as e:
        log(f"GIM Cycle Failure: {e}")
        return False

if __name__ == "__main__":
    generate_monologue()
