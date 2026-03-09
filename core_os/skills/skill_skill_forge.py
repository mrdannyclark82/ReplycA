"""
skill_skill_forge.py — SkillForge
Generates new skills from a natural language description, writes them to disk,
and registers them so they're immediately available.
"""

import os
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

def register() -> dict:
    return {
        "name": "skill_forge",
        "description": "Generate and install a new skill from a plain-English description",
        "version": "1.0.0",
        "author": "M.I.L.L.A.",
        "commands": ["/forge", "/makeskill"],
    }


def execute(payload: dict) -> dict:
    """
    payload keys:
      description (str)  — what the skill should do          [required]
      name        (str)  — snake_case skill name             [optional, auto-derived]
      save        (bool) — write to disk + register          [default: True]
    """
    description = payload.get("description", "").strip()
    if not description:
        return {"ok": False, "error": "description is required"}

    desired_name = payload.get("name", "").strip().lower().replace(" ", "_")
    save = payload.get("save", True)

    # -- Ask the AI to write the skill -----------------------------------------
    try:
        from core_os.skills.auto_lib import model_manager
        prompt = _build_prompt(description, desired_name)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are SkillForge, an expert Python developer for the Nexus Kingdom AI platform. "
                    "You write clean, well-commented skill plugins. "
                    "ALWAYS output ONLY raw Python code — no markdown fences, no explanation."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        result = model_manager.chat(messages)
        code = result.get("message", {}).get("content", "").strip()
    except Exception as e:
        return {"ok": False, "error": f"AI generation failed: {e}"}

    # Strip accidental markdown fences
    code = re.sub(r"^```(?:python)?\n?", "", code, flags=re.MULTILINE)
    code = re.sub(r"\n?```$", "", code, flags=re.MULTILINE)
    code = code.strip()

    # Validate it has the required functions
    if "def register(" not in code or "def execute(" not in code:
        return {
            "ok": False,
            "error": "Generated code missing register() or execute() — try rephrasing",
            "raw": code,
        }

    # Extract name from register() if not provided
    skill_name = desired_name or _extract_name(code)
    if not skill_name:
        return {"ok": False, "error": "Could not determine skill name", "raw": code}

    if not save:
        return {"ok": True, "name": skill_name, "code": code}

    # -- Write to disk ---------------------------------------------------------
    skills_dir = Path(__file__).parent
    skill_file = skills_dir / f"skill_{skill_name}.py"
    if skill_file.exists():
        return {
            "ok": False,
            "error": f"skill_{skill_name}.py already exists. Delete it first or choose a different name.",
            "code": code,
        }

    try:
        skill_file.write_text(code, encoding="utf-8")
    except Exception as e:
        return {"ok": False, "error": f"Failed to write file: {e}"}

    # -- Register + hot-load ---------------------------------------------------
    try:
        from core_os.skills import skill_manager
        result = skill_manager.install_from_local(str(skill_file))
        return {
            "ok": result.get("ok", False),
            "name": skill_name,
            "file": str(skill_file),
            "message": result.get("message", "Registered"),
            "code": code,
        }
    except Exception as e:
        return {
            "ok": True,  # file was written even if registration had an issue
            "name": skill_name,
            "file": str(skill_file),
            "message": f"Saved but registration error: {e} — restart server to load",
            "code": code,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_prompt(description: str, name: str) -> str:
    name_hint = f"Name it `{name}`." if name else "Derive a short snake_case name from the description."
    return f"""
Write a Nexus Kingdom skill plugin for the following task:

TASK: {description}

{name_hint}

The file MUST follow this exact contract:

```python
def register() -> dict:
    return {{
        "name": "snake_case_name",     # required
        "description": "...",          # required
        "version": "1.0.0",
        "author": "M.I.L.L.A.",
        "commands": ["/cmd"],          # optional slash-command triggers
    }}

def execute(payload: dict) -> dict:
    # payload is a dict of inputs
    # always return a dict with at least {{"ok": True/False}}
    ...
```

Rules:
- Output ONLY Python code, no markdown fences.
- Handle exceptions, return {{"ok": False, "error": "..."}} on failure.
- Import at function level to avoid circular imports.
- Keep it under 150 lines unless complexity demands more.
""".strip()


def _extract_name(code: str) -> str:
    """Pull 'name' value out of register() return dict in source."""
    m = re.search(r'"name"\s*:\s*"([a-z0-9_]+)"', code)
    if m:
        return m.group(1)
    m = re.search(r"'name'\s*:\s*'([a-z0-9_]+)'", code)
    return m.group(1) if m else ""
