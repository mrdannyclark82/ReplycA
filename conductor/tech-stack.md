# Tech Stack

## Primary Runtime
- Python (virtualenv)
- Node.js / TypeScript (Genkit, React/Vite, Electron)

## Architecture Layers
- **Core OS:** Python-based brain stem (`cortex.py`, `milla_nexus.py`) managing state, tools, and memory.
- **Frontend Dashboard:** React 19 + Vite 8 + Tailwind 4 (PWA) polling `/api/neuro`.
- **Backend Server:** FastAPI (`nexus_server.py`) serving endpoints and WebSocket connections.
- **AI Models:** Local Ollama (`qwen2.5-coder` models), Google AI (Gemini via Genkit), xAI (Grok).
- **Standalone Tools:** Ninja (Electron browser), Lazy (Code generator).

## Memory & State
- **Short-Term:** SQLite (`agent_memory.db`)
- **Long-Term:** SQLite (`milla_long_term.db`)
- **Context/Dialogue:** JSON (`shared_chat.jsonl`)
- **Bio-Vitals:** JSON (`neuro_state.json`)
