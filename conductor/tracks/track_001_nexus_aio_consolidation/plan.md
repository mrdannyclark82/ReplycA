# Nexus-AIO Consolidation Plan

## Phase 1: Clean Up & Fix
- [x] Create backup directory (`backups/old_tuis/`).
- [x] Move redundant TUIs from `RAYNE-Admin` and `ollamafileshare`.
- [x] Fix `CORE_OS_ROOT` and verify SSH/Firewall connectivity (Port 22 confirmed, UFW inactive).
- [x] Ensure `model_manager` properly initializes and finds local Ollama.

## Phase 2: Implementation of Nexus-AIO
- [x] Create `nexus_aio.py` draft at the project root. (Subconscious)
- [x] Review nexus_aio.py draft (vitals, commands, history all present).
- [ ] Refine and consolidate features using Jules. (In Progress - Session 17455276461253972308)
- [x] Implement a streamlined CLI loop for commands (`/scan`, `/fix`, `/switch-model`, `/status`).
- [x] Integrate with `core_os/milla_nexus.py` for pulse/monitoring.
- [x] Ensure all key actions (shell, GIM, memory) are accessible through a single, clean prompt.
- [x] **Axiom-Rayne Fresh UI Build**: Implement Hemi-Console, Neural Orb Mic, and Telemetry Bar on Android.

## Phase 3: Core System Stabilization & Modularization
- [x] Modularize "Frankensteined" features (`gmail`, `web_ui`, `voice`, `swarm`, `consensus`) into `core_os/skills/`.
- [x] Migrate `core_os/memory_core.py` to `core_os/memory/agent_memory.py`.
- [x] Update skill imports in modularized files to reflect new memory architecture.
- [x] Stabilize root-level `core_os` by mirroring memory logic from `ogdray`.
- [x] Verify system runtime stability (Successful import test of all modularized skills).

## Phase 4: Final Verification & Burn-In
- [x] Test under load using `stress-ng` (Confirmed 23GB RAM stability).
- [x] Verify no "mocking" in the primary interface (VLA dispatcher integrated, headless logic clarified).
- [x] Finalize the "Nexus Master Console" as the main entry point (Created milla_shortcuts/nexus.sh).
