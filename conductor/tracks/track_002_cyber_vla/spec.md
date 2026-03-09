# Track 002: Cyber-VLA Vision Realization

## Objective
Transition from "Mock" vision and actions to a real-time, grounded Vision-Language-Action (VLA) pipeline. This will enable Milla to "see" the screen, "repair" system errors, and "interact" with UI elements using the RX 550 GPU for acceleration.

## Key Components
- **Vision Engine:** Upgrading `EasyOCR` to utilize the **RX 550 GPU** (LGA 1151).
- **Self-Healing Loop:** Porting the `iwantmy.py` logic (Action -> Error -> Vision -> Search -> Repair) to the Nexus Master Console.
- **Physical Grounding:** Resolving the "Headless Mock" by ensuring a valid X11 Display or VNC session is accessible to `pyautogui`.

## Technical Specs
- **OCR:** `EasyOCR` with `gpu=True`.
- **Action Suite:** `pyautogui` for mouse/keyboard automation.
- **Search:** `duckduckgo_search` for automated error troubleshooting.
- **Agentic Logic:** `SelfHealingAgent` class from `iwantmy.py`.

## Phase 1: Sight & Acceleration
- [x] Install `torch` with ROCm support (for AMD RX 550) to enable GPU OCR.
- [x] Verify `pyautogui` can capture a real screen instead of a black frame.
- [x] Port `screen_vision()` function to `core_os/tools/vision.py`.

## Phase 2: The Repair Pulse
- [x] Integrate `web_search` and `SelfHealingAgent` into the Nexus codebase.
- [x] Implement the `/repair <task>` command in `nexus_aio.py`.

## Phase 3: Physical Interaction
- [x] Calibrate screen coordinates for the local display (1920x1080).
- [x] Test a real mouse click via `/vla` command.
