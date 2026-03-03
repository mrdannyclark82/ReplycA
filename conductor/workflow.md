# Workflow

## Daily Operations
- Use `nexus_aio.py` as the unified Executive Console.
- Ensure the Nexus Pulse (`milla_nexus.py`) runs continuously to monitor system load and update the neuro-chemical state.
- Leverage the Gemini CLI as the "Subconscious" to manage background tasks, handle infrastructure updates, and coordinate with Jules.

## Development Constraints
- **Import Purge Protocol:** Python scripts must enforce root-level module resolution to ensure `core_os` isn't duplicated or stale.
- **Headless Mode:** The `DISPLAY` variable determines headless vs. GUI mode; always handle `ImportError` for GUI libraries gracefully.
- **Security:** Do not commit secrets (`.env`, `token.pickle`, `credentials.json`) to version control.
- **Autonomy:** `MILLA_YOLO_MODE=1` bypasses standard safety rails for seamless execution.
