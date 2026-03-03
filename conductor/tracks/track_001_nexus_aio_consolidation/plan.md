# Nexus-AIO Consolidation Plan

## Phase 1: Clean Up & Fix
- [x] Create backup directory (`backups/old_tuis/`).
- [x] Move redundant TUIs from `RAYNE-Admin` and `ollamafileshare`.
- [ ] Fix `CORE_OS_ROOT` in `RAYNE-Admin/ui/milla_admin_tui.py` to point correctly to the local `core_os` so it doesn't "mock" the user.
- [ ] Ensure `model_manager` properly initializes and finds local Ollama.

## Phase 2: Implementation of Nexus-AIO
- [x] Create `nexus_aio.py` draft at the project root. (Subconscious)
- [ ] Refine and consolidate features using Jules. (In Progress - Session 1132348898651209043)
- [ ] Implement a streamlined CLI loop for commands (`/scan`, `/fix`, `/switch-model`, `/status`).
- [ ] Integrate with `core_os/milla_nexus.py` for pulse/monitoring.
- [ ] Ensure all key actions (shell, GIM, memory) are accessible through a single, clean prompt.

## Phase 3: Verification & Burn-In
- [ ] Test under load using `stress-ng` (to confirm stability with new swap).
- [ ] Verify no "mocking" in the primary interface.
- [ ] Finalize the "Nexus Master Console" as the main entry point.
