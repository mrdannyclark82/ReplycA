# M.I.L.L.A. R.A.Y.N.E. - Copilot Instructions

## Project Overview

This is **M.I.L.L.A. R.A.Y.N.E.** (Multi Integrated Large Language Admin - Running All Your Needs Executive) — an autonomous AI agent and system regulator built by Dray (The Architect). It is a co-evolutionary platform, not a standard chatbot app.

## Running the Project

```bash
# Activate the virtual environment first (always required)
source venv/bin/activate

# Primary entry point — the Nexus-AIO Kingdom Console
python nexus_aio.py

# Full agent with tool-call loop and voice support
python main.py
python main.py --voice          # hands-free voice mode
python main.py --service        # headless service/daemon mode

# Backend API server (FastAPI, port 8000)
python nexus_server.py

# Frontend dashboard (React/Vite, port 5173 — proxies /api and /ws to 8000)
cd new-nexus-dashboard && npm run dev
```

## Lint & CI

```bash
# Flake8 — only errors + warnings (max-line-length 127)
pip install flake8
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Frontend lint
cd new-nexus-dashboard && npm run lint
```

The CI pipeline (`.github/workflows/ci.yml`) runs on push/PR to `main`: installs `requirements.txt` then runs flake8 with the above settings.

## Architecture

```
nexus_aio.py          — Executive console; HUD, slash commands (/scan /fix /model /vla /repair /gim)
main.py               — Full agent loop with tool-call dispatch, voice, and cortex integration
nexus_server.py       — FastAPI backend: REST endpoints + WebSocket PTY terminal (port 8000)
new-nexus-dashboard/  — React 19 + Vite 8 + Tailwind 4 PWA frontend (port 5173)
core_os/              — The modular "brain stem"
  cortex.py           — Meta-cognition: classifies input state (CRISIS / BONDING / etc.)
  milla_nexus.py      — Background nexus_pulse (runs every 10 min via thread)
  skills/auto_lib.py  — ModelManager: Ollama primary, Gemini/xAI fallback; houses MILLA_SYSTEM_PROMPT
  skills/scout.py     — Scout sub-agent for system health scans and auto-fix
  skills/dynamic_features.py — Flask-based dynamic tool registration at runtime
  memory/history.py   — shared_chat.jsonl R/W (load_shared_history / append_shared_messages)
  memory/agent_memory.py     — SQLite short-term memory (agent_memory.db)
  memory/digital_humanoid.py — DigitalHumanoid: simulated neurochemistry (dopamine, serotonin, etc.)
  memory/neuro_state.json    — Live bio-vitals read by dashboard /api/neuro
  config/GEMINI.md    — Neuro-Orchestrator prompt spec: JSON output format for warped_query + chemistry
  actions/            — Tool functions passed directly to model_manager.chat(tools=[...])
conductor/            — Product docs, tech stack reference, workflow notes
lazy/                 — One-shot AI code generator; queries Ollama and saves output to lazy/output/
ninja/                — Electron-based privacy browser (npm start / npm run dev)
iwantmy.py            — Standalone SelfHealingAgent: EasyOCR vision + Ollama reasoning + subprocess action
```

### Sub-project entry points

| Sub-project | How to run |
|---|---|
| `lazy` | `./lazy/lazy/lazy` (or `lazy/setup.sh` first-time install) |
| `ninja` | `cd ninja && npm start` \| `npm run dev` |
| `iwantmy.py` | `python iwantmy.py` (requires `easyocr`, `ollama`, `pyautogui`, `duckduckgo_search`) |

## Key Conventions

**Import path management**: Every entry point manually inserts `PROJECT_ROOT` into `sys.path` and purges stale `core_os.*` module imports. If you add a new entry point, follow the same pattern at the top of the file.

**Headless / no-display guard**: `main.py` checks `os.environ.get("DISPLAY")` at startup and pre-mocks GUI modules (`tkinter`, `pyautogui`, etc.) before any imports. `nexus_aio.py` sets `os.environ["DISPLAY"] = ""` unconditionally. GUI-dependent tools must be wrapped in a `try/except ImportError` and replaced with lambda mocks.

**Tool dispatch**: Tools are plain Python functions registered in the `base_tools` list and passed as `tools=` to `model_manager.chat()`. The model drives tool-calling; `main.py` and `nexus_aio.py` handle the loop. New tools go in `core_os/actions/` and are imported/appended in `main.py`.

**ModelManager (`auto_lib.py`)**: Primary backend is **xAI (`grok-4-latest`)**, read from `XAI_MODEL` env var. Ollama (`qwen2.5-coder:1.5b`) is the local fallback when no `XAI_API_KEY` is present. Switch at runtime with `/model <name>`. Keys come from `.env` via `python-dotenv`.

**Neurochemical state**: `DigitalHumanoid` simulates dopamine, serotonin, cortisol, oxytocin, etc. The state is ticked on every `agent_respond()` call, written to `neuro_state.json`, and exposed via `/api/neuro`. The `executive_refinement()` function in `main.py` alters responses when cortisol > 0.7.

**Shared history**: All interaction history is stored in `core_os/memory/shared_chat.jsonl` (newline-delimited JSON). Both the CLI agent and the dashboard backend write to this file. Load with `load_shared_history(limit=N)`.

**Slash commands (nexus_aio.py)**: `/scan`, `/fix [idx|all]`, `/model [name]`, `/history`, `/status`, `/gim`, `/vla <goal>`, `/repair <task>`. Bare `!command` runs a shell command via `terminal_executor`.

**Environment**: Secrets live in `.env` (never committed — see TODO.md). Required keys include `GEMINI_API_KEY`, `XAI_API_KEY`, and Google OAuth credentials (`client_secret.json`, `token.pickle`).

**Frontend ↔ Backend**: Vite proxies `/api` and `/ws` to `localhost:8000`. Always use relative paths (`/api/...`) in the React frontend. The dashboard polls `/api/neuro` for live bio-vitals.

**Two senses**: The global `STATE["sense"]` in `nexus_server.py` toggles between `"synesthetic"` (data/code feeling) and `"optical"` (visual environment analysis via `milla_vision.py` + moondream model).

**Neuro-Orchestrator JSON contract** (`core_os/config/GEMINI.md`): The cortex layer expects the model to return strictly valid JSON with this shape when processing inputs:
```json
{
  "chemistry": {"d": float, "s": float, "n": float},
  "params":    {"temp": float, "rep_penalty": float},
  "content":   "Rewritten prompt or Dream Insight",
  "state_label": "CRISIS | STABLE | EXPLORATORY"
}
```
In `ACTIVE` mode the model rewrites the user prompt as `warped_query` and adjusts inference params. In `DREAM` mode (00:00–06:00 REM cycles) it synthesizes long-term insights from vision/text logs. If the screen shows an error, Norepinephrine (`n`) should spike.

**Sub-project GEMINI.md files**: Each major sub-project may contain its own `GEMINI.md` providing context specific to that area (e.g., `ollamafileshare/GEMINI.md`). Check for these before working inside a sub-directory.

## Sensitive Files — Do Not Commit

- `.env`
- `client_secret.json`
- `token.pickle`
- `credentials.json`
- `core_os/memory/security_data/`
