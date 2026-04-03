# M.I.L.L.A. R.A.Y.N.E. / ogdray — Copilot Instructions

## Project overview

This repository is a hybrid workspace centered on the Python-based M.I.L.L.A. R.A.Y.N.E. runtime, with a small Genkit TypeScript layer at the root and two active nested projects: `new-nexus-dashboard/` for the Vite UI and `deer-flow/` / `Milla-Deer/` for parallel agent stacks.

The main tracked backend surfaces for the root project are:

- `src/core/` for the Python entrypoints (`main.py`, `nexus_aio.py`, `nexus_server.py`)
- `core_os/` for the shared runtime, tools, memory, and cortex logic
- `new-nexus-dashboard/` for the React dashboard that talks to the FastAPI backend
- `src/index.ts` for the separate Genkit-based tool runner

If you are working inside `deer-flow/`, use `deer-flow/.github/copilot-instructions.md` first. That subtree also has local assistant guidance in `deer-flow/backend/AGENTS.md`, `deer-flow/backend/CLAUDE.md`, `deer-flow/frontend/AGENTS.md`, and `deer-flow/frontend/CLAUDE.md`.

The repo root also includes `.mcp.json`, which configures a shared Playwright MCP server for browser work across the active web surfaces in this workspace.

## Build, test, lint, and run commands

### Root Python runtime

The root repo CI only installs `requirements.txt` and runs `flake8` from `.github/workflows/ci.yml`.

```bash
source venv/bin/activate

# CI-equivalent lint
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

Important: many docs and service files still reference historical repo-root scripts such as `python nexus_aio.py`, `python main.py`, and `python nexus_server.py`, but the tracked sources now live under `src/core/`. Before changing startup commands, verify whether a local machine still has untracked wrappers. If you need to run the tracked files directly, do it from the repo root so `core_os/` resolves correctly.

There is no maintained repo-level automated test command for the root Python runtime. `src/tests/` contains ad hoc Python test files, but neither CI nor a checked-in Python test config wires them into a standard suite.

### Root TypeScript / Genkit layer

From `/home/nexus/ogdray`:

```bash
npm run dev
```

- `npm run dev` runs `tsx --watch src/index.ts`
- `npm test` is a placeholder in the root `package.json` and intentionally exits with an error
- there is no root `lint` or `build` script in `package.json`

### Dashboard: `new-nexus-dashboard/`

```bash
cd new-nexus-dashboard
npm run dev
npm run build
npm run lint
```

- Dev server is Vite on port `5175`, not `5173`
- `vite.config.ts` proxies `/api` to `http://localhost:8000` and `/ws` to `ws://localhost:8000`
- there is no test script in this package

### Nested project: `deer-flow/`

Use the root `Makefile` for full-stack orchestration:

```bash
cd deer-flow
make check
make install
make dev
make stop
```

Backend validation lives in `deer-flow/backend/Makefile`:

```bash
cd deer-flow/backend
make lint
make test

# Single test
PYTHONPATH=. uv run pytest tests/test_<feature>.py -v
```

### Nested project: `Milla-Deer/`

The workspace root routes most commands into `Milla-Deer/Milla-Rayne`, which the README identifies as the primary full-stack app:

```bash
cd Milla-Deer
pnpm run dev
pnpm run check
pnpm run lint
pnpm run test
pnpm run build
```

For direct test targeting, run the package command in `Milla-Deer/Milla-Rayne/`:

```bash
cd Milla-Deer/Milla-Rayne
npx --yes vitest run --config ./vitest.config.server.ts server/__tests__/avRag.test.ts
```

`pnpm run test` at the workspace root is a smoke suite, not the full Vitest run. Use `test:full` in `Milla-Deer/Milla-Rayne/package.json` when you need broader coverage.

### Playwright MCP targets

The shared Playwright MCP config at the repo root is meant to pair with these dev servers:

- `new-nexus-dashboard/` via `npm run dev` on `https://localhost:5175`
- `deer-flow/` via `make dev` on `http://localhost:2026`
- `Milla-Deer/` via `pnpm run dev` / `pnpm run dev:all`, typically on `http://localhost:5000`

The current root `.mcp.json` launches Playwright via `npx`. On a clean machine, the first run may need to fetch `@automatalabs/mcp-server-playwright`, so do not assume the binary is already available offline.

## High-level architecture

### Root runtime

- `src/core/main.py` is the conversational CLI agent. It assembles `base_tools`, runs input through `core_os.cortex`, calls `model_manager.chat(...)`, then applies `executive_refinement()` before persisting history.
- `src/core/nexus_aio.py` is the command-oriented executive console. It handles slash commands like `/scan`, `/fix`, `/model`, `/history`, `/status`, `/gim`, `/vla`, and `/repair`, and it starts the background `nexus_pulse()`.
- `src/core/nexus_server.py` is the FastAPI backend for the dashboard. It serves `/api/neuro`, `/api/history`, `/api/chat`, sense switching, OAuth, and PTY/WebSocket-backed terminal features.

### Shared Python runtime

- `core_os/skills/auto_lib.py` contains `model_manager`, loads `.env` with `override=True`, and owns the provider-selection logic.
- `core_os/cortex.py` is a fast heuristic layer that turns user text into neurochemical state plus an executive instruction.
- `core_os/memory/` is the shared persistence layer: `shared_chat.jsonl` for cross-surface history, `agent_memory.db` for short-term memory, `milla_long_term.db` for long-term recall, and `neuro_state.json` for live state consumed by the dashboard.
- `core_os/actions/` holds tool functions used by the CLI/runtime; `nexus_server.py` also exposes a separate API-facing tool list for web chat.

### Frontend and secondary runtimes

- `new-nexus-dashboard/` is a standalone React 19 + Vite 8 dashboard. It is not bundled with the Python app; it depends on the FastAPI backend already running on port `8000`.
- `src/index.ts` is a separate Genkit-based runner that defines `terminalExecutor`, `toolWriter`, and `nexusAgentFlow`. Treat it as an alternate integration surface, not the main backend.
- `deer-flow/` is an active LangGraph-based platform with its own build, test, and onboarding instructions.
- `Milla-Deer/` is an active pnpm workspace where `Milla-Rayne/` is the primary web/server package and `Deer-Milla/` is the canonical mobile client.

## Key conventions

### `core_os` path handling is fragile and deliberate

The root runtime assumes there is exactly one authoritative `core_os/` tree. Python entrypoints manually manipulate `sys.path`, and `nexus_aio.py` also purges stale `core_os*` modules from `sys.modules`. When adding scripts or moving entrypoints, preserve that pattern and run from the repo root instead of copying modules into subdirectories.

### Docs and deployment files still reference the historical root layout

README files, `src/docs/instructions.md`, `milla_shortcuts/nexus.sh`, and `mea_os/autostart/*.service` still point at repo-root files like `nexus_aio.py` and `nexus_server.py`. The tracked implementations are under `src/core/`. Treat this as an active migration seam and verify the real deployment path before "fixing" either side.

### Headless mode is a first-class runtime mode

`src/core/main.py` pre-mocks GUI-related modules when `DISPLAY` is unset. New GUI-dependent tooling should follow the same import-guard pattern instead of assuming X11/desktop access exists.

### The dashboard only works with relative API paths

Keep frontend calls on `/api/...` and `/ws/...`. `new-nexus-dashboard/vite.config.ts` owns the dev proxy to port `8000`; hardcoded hostnames or ports in components will break local development.

### The neuro-state file is shared infrastructure

`core_os/cortex.py` writes `core_os/memory/neuro_state.json`, `src/core/main.py` uses it for response refinement, `src/core/nexus_aio.py` renders it in the HUD, and `src/core/nexus_server.py` exposes it via `/api/neuro`. Changes to that schema ripple across CLI, API, and dashboard surfaces.

### Tool wiring happens in more than one place

- CLI/runtime tools are added in `core_os/actions/` and assembled into `base_tools` in `src/core/main.py`
- Web-chat tools are separately declared in `src/core/nexus_server.py` as JSON tool definitions plus a local dispatcher

If you add a capability that should exist in both CLI and web chat, wire both layers.

### Provider defaults are code-driven, not README-driven

`core_os/skills/auto_lib.py` currently prefers Ollama when the Python `ollama` package is available and falls back to xAI only when Ollama is unavailable. `.env.example` expects `OLLAMA_MODEL=milla-rayne`, `MILLA_BASE_MODEL=qwen2.5-coder:7b`, and `XAI_MODEL=grok-4-latest`. Prefer the code and `.env.example` over older prose docs when these disagree.

### Secrets and stateful local files must stay out of commits

Never commit `.env`, `client_secret.json`, `token.pickle`, generated database files, or chat/memory artifacts under `core_os/memory/`.
