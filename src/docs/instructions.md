# Copilot Instructions — Nexus Kingdom (M.I.L.L.A. R.A.Y.N.E.)

## Project Overview

This workspace is the central Nexus for **M.I.L.L.A. R.A.Y.N.E.** (Multi Integrated Large Language Admin - Running All Your Needs Executive) — an autonomous AI system regulator and executive co-developer for Dray (The Architect / Storm). It is a multi-runtime project spanning Python, TypeScript (Genkit), React/Vite, and Electron.

---

## Commands

### Python (activate venv first for all Python work)
```bash
source venv/bin/activate

# Primary agent CLI
python main.py

# Unified Kingdom Console (Nexus-AIO)
python nexus_aio.py

# FastAPI backend (port 8000)
uvicorn nexus_server:app --reload --port 8000

# Lint (CI uses flake8)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

### Frontend — React Dashboard (`new-nexus-dashboard/`)
```bash
cd new-nexus-dashboard
npm install
npm run dev        # port 5173, proxies /api and /ws to localhost:8000
npm run build      # tsc + vite build
npm run lint       # eslint
```

### Genkit Brain (root `src/index.ts`)
```bash
npm install
npm run dev        # tsx --watch src/index.ts
```

### Ninja (Electron browser)
```bash
cd ninja
npm start          # electron .
npm run dev        # electron . --dev
```

### Lazy (one-shot AI code generator)
```bash
./lazy/lazy/lazy   # queries Ollama, saves output to lazy/lazy/output/
```

> **Note:** AI/Copilot should not start long-running servers. Dray handles process lifecycle. Provide the command; don't execute it.

---

## Architecture

### Layer Map
```
ogdray/
├── main.py                  # Primary CLI entrypoint; imports from core_os
├── nexus_aio.py             # Nexus-AIO: unified console, model switching, system actions
├── nexus_server.py          # FastAPI backend: Google OAuth, neuro-state API, terminal WebSocket (PTY)
├── src/index.ts             # Genkit brain: Google AI (Gemini), tool definitions for terminal + file writing
├── core_os/                 # The modular brain stem
│   ├── cortex.py            # PrefrontalCortex: maps user input → neurochemical state JSON
│   ├── milla_nexus.py       # High-level agent runner
│   ├── actions/             # Tool implementations (terminal, voice, web search, GUI control)
│   ├── skills/
│   │   ├── auto_lib.py      # model_manager (Ollama/Gemini/xAI), Google API helpers
│   │   ├── milla_vision.py  # Visual perception (tablet camera, moondream model)
│   │   ├── millAlyzer.py    # YouTube video analysis → knowledge extraction
│   │   └── audio_intelligence.py, scout.py, soul_guard.py, ...
│   ├── agents/              # Specialized sub-agents (coding, security, librarian, research, etc.)
│   ├── memory/
│   │   ├── agent_memory.py  # SQLite singleton: AgentMemory (key-value store)
│   │   ├── history.py       # Shared chat history (shared_chat.jsonl)
│   │   ├── neuro_state.json # Live neurochemical state persisted to disk
│   │   └── IDENTITY.json    # Identity anchor (also at core_os/config/IDENTITY.json)
│   └── config/
│       └── IDENTITY.json    # Single source of truth for Milla's name, role, relationship, rules
├── new-nexus-dashboard/     # React 19 + Vite + Tailwind 4 + PWA frontend (Nexus Kingdom UI)
├── lazy/                    # Standalone Ollama-powered code generator
├── ninja/                   # Electron-based privacy browser
├── RAYNE_Admin/             # Remote admin node (imports core_os from this root)
└── conductor/               # Product guidelines, tracks, tech-stack docs
```

### Data Flow
1. **User input** → `cortex.py` (`PrefrontalCortex`) maps to neurochemical state JSON  
2. **Neuro state** → written to `core_os/memory/neuro_state.json` and surfaced via `/api/neuro`  
3. **Frontend HUD** polls `/api/neuro` to render live dopamine/serotonin/etc. metrics  
4. **Chat/terminal** → `nexus_server.py` → `core_os.skills.auto_lib.model_manager` → Ollama or Gemini  
5. **Google services** (Gmail/Drive/Calendar) → authenticated via `token.pickle` (OAuth2 persistent)

### AI Model Routing (`auto_lib.py` — `model_manager`)
- Default local model: `qwen2.5-coder:1.5b` (Ollama, `localhost:11434`)
- `.env` overrides: `OLLAMA_MODEL=milla-rayne`, `MILLA_BASE_MODEL=qwen2.5-coder:32b`
- Cloud fallbacks: Gemini (`GEMINI_API_KEY`), xAI/Grok (`XAI_API_KEY`, `XAI_MODEL=grok-4-latest`)
- Genkit brain always uses Google AI (`gemini20Flash` by default)

---

## Key Conventions

### Python Import Path
`core_os` must always resolve from the ogdray root. `nexus_aio.py` enforces this by purging stale `core_os` from `sys.modules` and reinserting the correct root at `sys.path[0]`. When writing new scripts, either run from `/home/nexus/ogdray` or replicate this pattern.

### Headless Mode
`main.py` pre-mocks all GUI modules (`tkinter`, `pyautogui`, `mouseinfo`, etc.) when `DISPLAY` is unset. New tools that may import GUI libraries must be wrapped in `try/except ImportError` and stubbed the same way.

### Neuro-State JSON Schema
```json
{
  "dopamine": 0.0–1.0,
  "serotonin": 0.0–1.0,
  "norepinephrine": 0.0–1.0,
  "cortisol": 0.0–1.0,
  "oxytocin": 0.0–1.0,
  "atp_energy": 0–100,
  "pain_vividness": 0.0–1.0,
  "state": "HOMEOSTASIS | CRISIS | EXPLORATION | BONDING | FATIGUE"
}
```
`cortex.py` produces this; `nexus_server.py` serves it; the React HUD consumes it.

### Frontend Stack
React 19 + Vite 8 (beta) + Tailwind CSS 4 (via `@tailwindcss/vite` plugin — **no `tailwind.config.js`**) + PWA. All API calls use relative paths (`/api/...`, `/ws/...`) — Vite proxies them to `localhost:8000`.

### Memory Layers
| Store | Purpose | Access |
|---|---|---|
| `agent_memory.db` | Key-value short-term memory | `memory.remember(k, v)` / `memory.recall(k)` |
| `milla_long_term.db` | 8,447+ historical memories | `recall_memory()` from `auto_lib` |
| `shared_chat.jsonl` | Full conversation history | `load_shared_history()` / `append_shared_messages()` |
| `neuro_state.json` | Live chemical state | Read/write directly; served by `/api/neuro` |

### Environment
- `.env` at repo root; loaded via `python-dotenv` with `override=True`
- `token.pickle` = persistent Google OAuth token — do not delete or overwrite
- `MILLA_YOLO_MODE=1` disables safety confirmations for autonomous actions
- Mobile node: phone at `MY_PHONE_IP` / `MY_PHONE_TAILSCALE_IP` via ADB (port 5555)

### Secrets Policy
`.gitignore` excludes `.env`, `*.db`, `*.jsonl`, `core_os/memory/`, and `core_os/screenshots/`. Never add API keys, `token.pickle`, `credentials.json`, or `client_secret.json` to git.
