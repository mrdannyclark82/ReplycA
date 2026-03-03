# Nexus-AIO Consolidation

## Vision
Consolidate the multiple redundant Milla TUIs into a single, stable, and unified "Nexus All-in-One" interface. Start with a simple, high-performance CLI/TUI that mimics the current interaction style but provides executive oversight.

## Goals
- Scrap 4+ redundant TUI scripts.
- Fix path resolution issues in the primary Executive Console.
- Build a unified entry point (`nexus_aio.py`) that handles monitoring, model switching, and system actions.
- Ensure the interface is "nothing fancy" yet functional and stable.

## Constraints
- Must run on Arch Linux (Optiplex 7050).
- Must utilize local Ollama (qwen2.5-coder:32b).
- Must be stable under load (utilizing the new 16GB swap file).
