# Nexus Kingdom - Save Point (March 1, 2026)

## Current State
- **Backend (`nexus_server.py`):** Configured for FastAPI. Includes Google OAuth, Neuro-state API, and Terminal WebSocket (PTY).
- **Frontend (`new-nexus-dashboard`):** React/Vite/TS project.
- **Tailwind 4.0:** Fully installed and configured via `@tailwindcss/vite`.
- **Connectivity:** All components updated to use relative paths (`/api/...`, `/ws/...`) to support Vite proxying.

## Server Configuration

- **Backend Port:** 8000 — `python nexus_server.py`
- **Frontend Port:** 5173 — `cd new-nexus-dashboard && npm run dev` (proxies `/api` and `/ws` to 8000)
