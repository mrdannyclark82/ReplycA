"""
skill_manager.py — Nexus Kingdom Skill Plugin System
Installs, loads, and executes skills from GitHub or local paths.

Skill contract: each skill file must expose:
  def register() -> dict:  # metadata
  def execute(payload: dict) -> dict:  # entry point

register() must return at minimum: {name, description, version}
Optional keys: author, commands (list of /cmd triggers), requires (pip deps)
"""

import os
import sys
import json
import importlib
import importlib.util
import subprocess
import re
import logging
from pathlib import Path
from typing import Optional

SKILLS_DIR   = Path(__file__).parent                     # core_os/skills/
REGISTRY_PATH = Path(__file__).parent.parent / "memory" / "skills_registry.json"

logger = logging.getLogger("skill_manager")


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------

def _load_registry() -> dict:
    if REGISTRY_PATH.exists():
        try:
            return json.loads(REGISTRY_PATH.read_text())
        except Exception:
            pass
    return {}


def _save_registry(reg: dict):
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(reg, indent=2))


# ---------------------------------------------------------------------------
# In-memory loaded modules  { skill_name: module }
# ---------------------------------------------------------------------------
_loaded: dict = {}


def _skill_path(name: str) -> Path:
    return SKILLS_DIR / f"skill_{name}.py"


# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------

def install_from_github(url: str) -> dict:
    """
    Accepts:
      - Full raw URL:  https://raw.githubusercontent.com/user/repo/main/skill_thing.py
      - Repo URL:      https://github.com/user/repo  (grabs first *.py with register())
      - Short form:    user/repo/path/to/skill.py
    Returns: {"ok": bool, "name": str, "message": str}
    """
    raw_url = _resolve_raw_url(url)
    if not raw_url:
        return {"ok": False, "name": "", "message": f"Cannot resolve raw URL from: {url}"}

    # Download
    try:
        import urllib.request
        code, _ = urllib.request.urlretrieve(raw_url)
        source = Path(code).read_text(encoding="utf-8")
    except Exception as e:
        return {"ok": False, "name": "", "message": f"Download failed: {e}"}

    return _install_from_source(source, origin=raw_url)


def install_from_local(file_path: str) -> dict:
    """Install a skill from a local .py file path."""
    p = Path(file_path)
    if not p.exists():
        return {"ok": False, "name": "", "message": f"File not found: {file_path}"}
    return _install_from_source(p.read_text(encoding="utf-8"), origin=file_path)


def _install_from_source(source: str, origin: str) -> dict:
    # Validate: must have register() and execute()
    if "def register(" not in source:
        return {"ok": False, "name": "", "message": "Skill missing register() function"}
    if "def execute(" not in source:
        return {"ok": False, "name": "", "message": "Skill missing execute() function"}

    # Exec in temp namespace to get metadata
    ns: dict = {}
    try:
        exec(compile(source, "<skill>", "exec"), ns)  # noqa: S102
        meta = ns["register"]()
    except Exception as e:
        return {"ok": False, "name": "", "message": f"register() failed: {e}"}

    name = meta.get("name", "").strip().lower().replace(" ", "_")
    if not name or not re.match(r'^[a-z0-9_]+$', name):
        return {"ok": False, "name": "", "message": "register() must return a valid 'name' (alphanumeric/underscore)"}

    # Install pip requirements
    requires = meta.get("requires", [])
    if requires:
        logger.info(f"[SkillManager] Installing deps for {name}: {requires}")
        try:
            pip = [sys.executable, "-m", "pip", "install", "--quiet"] + requires
            result = subprocess.run(pip, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                logger.warning(f"[SkillManager] pip warning: {result.stderr[:300]}")
        except Exception as e:
            return {"ok": False, "name": name, "message": f"pip install failed: {e}"}

    # Write skill file
    dest = _skill_path(name)
    dest.write_text(source, encoding="utf-8")

    # Update registry
    reg = _load_registry()
    reg[name] = {
        "name":        name,
        "description": meta.get("description", ""),
        "version":     meta.get("version", "0.0.1"),
        "author":      meta.get("author", "unknown"),
        "commands":    meta.get("commands", []),
        "requires":    requires,
        "origin":      origin,
        "enabled":     True,
    }
    _save_registry(reg)

    # Hot-load
    _hot_load(name)

    return {"ok": True, "name": name, "message": f"Skill '{name}' installed and loaded.", "meta": reg[name]}


# ---------------------------------------------------------------------------
# Hot-load / unload
# ---------------------------------------------------------------------------

def _hot_load(name: str) -> bool:
    path = _skill_path(name)
    if not path.exists():
        return False
    spec = importlib.util.spec_from_file_location(f"skill_{name}", path)
    mod  = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        _loaded[name] = mod
        return True
    except Exception as e:
        logger.error(f"[SkillManager] Hot-load failed for {name}: {e}")
        return False


def load_all_enabled():
    """Called at server startup to load all enabled skills."""
    reg = _load_registry()
    for name, info in reg.items():
        if info.get("enabled", True):
            ok = _hot_load(name)
            logger.info(f"[SkillManager] {'✓' if ok else '✗'} {name}")


# ---------------------------------------------------------------------------
# Execute
# ---------------------------------------------------------------------------

def execute_skill(name: str, payload: dict) -> dict:
    reg = _load_registry()
    if name not in reg:
        return {"ok": False, "error": f"Skill '{name}' not found"}
    if not reg[name].get("enabled", True):
        return {"ok": False, "error": f"Skill '{name}' is disabled"}

    if name not in _loaded:
        if not _hot_load(name):
            return {"ok": False, "error": f"Skill '{name}' failed to load"}

    mod = _loaded[name]
    if not hasattr(mod, "execute"):
        return {"ok": False, "error": f"Skill '{name}' has no execute() function"}

    try:
        result = mod.execute(payload)
        return {"ok": True, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# List / toggle / uninstall
# ---------------------------------------------------------------------------

def list_skills() -> list:
    reg = _load_registry()
    out = []
    for name, info in reg.items():
        out.append({**info, "loaded": name in _loaded})
    return out


def toggle_skill(name: str, enabled: bool) -> dict:
    reg = _load_registry()
    if name not in reg:
        return {"ok": False, "error": f"Skill '{name}' not found"}
    reg[name]["enabled"] = enabled
    _save_registry(reg)
    if not enabled and name in _loaded:
        del _loaded[name]
    elif enabled:
        _hot_load(name)
    return {"ok": True, "name": name, "enabled": enabled}


def uninstall_skill(name: str) -> dict:
    reg = _load_registry()
    if name not in reg:
        return {"ok": False, "error": f"Skill '{name}' not found"}
    # Remove file
    p = _skill_path(name)
    if p.exists():
        p.unlink()
    # Remove from registry + memory
    del reg[name]
    _save_registry(reg)
    _loaded.pop(name, None)
    return {"ok": True, "message": f"Skill '{name}' uninstalled."}


# ---------------------------------------------------------------------------
# URL resolver
# ---------------------------------------------------------------------------

def _resolve_raw_url(url: str) -> Optional[str]:
    """Convert any GitHub URL form to a raw.githubusercontent.com URL."""
    # Already raw
    if url.startswith("https://raw.githubusercontent.com"):
        return url
    # GitHub blob URL → raw
    m = re.match(r'https://github\.com/([^/]+)/([^/]+)/blob/(.+)', url)
    if m:
        return f"https://raw.githubusercontent.com/{m.group(1)}/{m.group(2)}/{m.group(3)}"
    # Short form: user/repo/path/to/file.py  (assumes main branch)
    m = re.match(r'^([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)/(.+\.py)$', url)
    if m:
        return f"https://raw.githubusercontent.com/{m.group(1)}/{m.group(2)}/main/{m.group(3)}"
    # Repo root: user/repo or https://github.com/user/repo  → try to find a skill file
    m = re.match(r'^(?:https://github\.com/)?([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)/?$', url)
    if m:
        # Try common skill file names
        user, repo = m.group(1), m.group(2)
        for fname in [f"{repo}.py", "skill.py", "main.py"]:
            candidate = f"https://raw.githubusercontent.com/{user}/{repo}/main/{fname}"
            try:
                import urllib.request
                urllib.request.urlopen(candidate, timeout=5)  # noqa: S310
                return candidate
            except Exception:
                pass
    return None
