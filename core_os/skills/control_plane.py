from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

try:
    from fastmcp import FastMCP
except Exception:
    FastMCP = None

try:
    import easyocr
except Exception:
    easyocr = None

try:
    from PIL import Image
except Exception:
    Image = None

from core_os.skills.milla_vision import analyze_visuals

VisionProfile = Literal["bitvla", "vlm-3r", "v2drop"]
AgentRole = Literal["Milla-System-Admin", "Milla-Coder"]

_OCR_READER = None


class FocusRegion(BaseModel):
    label: str
    x: int
    y: int
    width: int
    height: int
    source: Literal["ocr", "heuristic"]
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class DesktopContextRequest(BaseModel):
    prompt: str = "Summarize the desktop and active terminal state."
    vision_profile: VisionProfile = "vlm-3r"
    include_ocr: bool = True
    use_focus_regions: bool = True
    terminal_log_path: str | None = None
    tail_lines: int = Field(default=60, ge=1, le=400)


class DesktopContextSnapshot(BaseModel):
    prompt: str
    vision_profile: VisionProfile
    screenshot_path: str | None = None
    screen_size: dict[str, int] = Field(default_factory=dict)
    visual_summary: str = ""
    ocr_text: str = ""
    terminal_log_excerpt: str = ""
    focus_regions: list[FocusRegion] = Field(default_factory=list)
    engine_metadata: dict[str, Any] = Field(default_factory=dict)


class TerminalActionRequest(BaseModel):
    command: str
    cwd: str | None = None
    prompt: str | None = None
    vision_profile: VisionProfile = "vlm-3r"
    include_ocr: bool = True
    terminal_log_path: str | None = None
    tail_lines: int = Field(default=80, ge=1, le=400)
    capture_before: bool = True
    capture_after: bool = True


class TerminalActionResult(BaseModel):
    command: str
    cwd: str | None = None
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    before_context: DesktopContextSnapshot | None = None
    after_context: DesktopContextSnapshot | None = None


class AgentHandoffRequest(BaseModel):
    objective: str
    command: str | None = None
    cwd: str | None = None
    terminal_log_path: str | None = None
    vision_profile: VisionProfile = "vlm-3r"
    execute: bool = False


class AgentHandoffStep(BaseModel):
    agent: AgentRole
    action: str
    summary: str
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentHandoffResult(BaseModel):
    objective: str
    steps: list[AgentHandoffStep]
    execution: TerminalActionResult | None = None
    final_summary: str


def _get_ocr_reader():
    global _OCR_READER
    if _OCR_READER is None and easyocr is not None:
        _OCR_READER = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _OCR_READER


def _capture_display_frame() -> str | None:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        path = handle.name

    env = {**os.environ, "DISPLAY": os.getenv("DISPLAY", ":0.0")}
    try:
        subprocess.run(
            ["gnome-screenshot", "-f", path],
            timeout=5,
            check=True,
            env=env,
            capture_output=True,
            text=True,
        )
        return path
    except Exception:
        pass

    try:
        subprocess.run(
            ["import", "-window", "root", path],
            timeout=5,
            check=True,
            env=env,
            capture_output=True,
            text=True,
        )
        return path
    except Exception:
        pass

    try:
        from core_os.skills.milla_vision import capture_frame

        fallback = capture_frame()
        if fallback and os.path.exists(fallback):
            shutil.copyfile(fallback, path)
            return path
    except Exception:
        pass

    try:
        os.unlink(path)
    except OSError:
        pass
    return None


def _read_terminal_excerpt(log_path: str | None, tail_lines: int) -> str:
    if not log_path:
        return ""

    path = Path(log_path).expanduser()
    if not path.exists() or not path.is_file():
        return ""

    try:
        lines = path.read_text(errors="replace").splitlines()
    except Exception:
        return ""
    return "\n".join(lines[-tail_lines:])


def _get_image_size(image_path: str | None) -> dict[str, int]:
    if not image_path or not Image:
        return {}
    try:
        with Image.open(image_path) as image:
            width, height = image.size
        return {"width": width, "height": height}
    except Exception:
        return {}


def _profile_prompt(prompt: str, profile: VisionProfile) -> str:
    prefixes = {
        "bitvla": (
            "Focus on actionable controls, active panes, inputs, and click-worthy UI affordances. "
            "Describe them with lightweight directness for low-memory control."
        ),
        "vlm-3r": (
            "Emphasize spatial reasoning. Describe window layout, relative positions, overlapping panes, "
            "button placement, and where the user's attention should move next."
        ),
        "v2drop": (
            "Prioritize only the most informative visual tokens: terminal errors, warnings, dialogs, active cursor zones, "
            "and compact high-signal regions. Ignore decorative clutter."
        ),
    }
    return f"{prefixes[profile]}\n\nUser goal: {prompt}"


def _collect_focus_regions(
    image_path: str | None,
    image_size: dict[str, int],
    include_ocr: bool,
) -> tuple[list[FocusRegion], str]:
    regions: list[FocusRegion] = []
    ocr_text = ""

    if include_ocr and image_path:
        reader = _get_ocr_reader()
        if reader is not None:
            try:
                raw_results = reader.readtext(image_path, detail=1)
                text_lines = []
                for bbox, text, confidence in raw_results[:60]:
                    text_lines.append(text)
                    x0 = int(min(point[0] for point in bbox))
                    y0 = int(min(point[1] for point in bbox))
                    x1 = int(max(point[0] for point in bbox))
                    y1 = int(max(point[1] for point in bbox))
                    width = max(1, x1 - x0)
                    height = max(1, y1 - y0)
                    if width < 24 or height < 12:
                        continue
                    regions.append(
                        FocusRegion(
                            label=f"text:{text[:40]}",
                            x=x0,
                            y=y0,
                            width=width,
                            height=height,
                            source="ocr",
                            confidence=max(0.0, min(float(confidence), 1.0)),
                        )
                    )
                ocr_text = "\n".join(text_lines[:80])
            except Exception:
                ocr_text = ""

    if not image_size:
        return regions[:6], ocr_text

    width = image_size.get("width", 0)
    height = image_size.get("height", 0)
    if not width or not height:
        return regions[:6], ocr_text

    heuristic_regions = [
        FocusRegion(
            label="active-pane-center",
            x=max(0, int(width * 0.2)),
            y=max(0, int(height * 0.18)),
            width=max(1, int(width * 0.6)),
            height=max(1, int(height * 0.48)),
            source="heuristic",
            confidence=0.42,
        ),
        FocusRegion(
            label="terminal-lower-band",
            x=0,
            y=max(0, int(height * 0.58)),
            width=width,
            height=max(1, int(height * 0.34)),
            source="heuristic",
            confidence=0.38,
        ),
    ]
    regions.extend(heuristic_regions)
    return regions[:6], ocr_text


def _crop_focus_regions(image_path: str, regions: list[FocusRegion], limit: int = 2) -> list[tuple[FocusRegion, str]]:
    if not Image or not image_path or not os.path.exists(image_path):
        return []

    crops: list[tuple[FocusRegion, str]] = []
    with Image.open(image_path) as image:
        for region in regions[:limit]:
            left = max(0, region.x)
            top = max(0, region.y)
            right = min(image.width, region.x + region.width)
            bottom = min(image.height, region.y + region.height)
            if right <= left or bottom <= top:
                continue
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
                crop_path = handle.name
            image.crop((left, top, right, bottom)).save(crop_path)
            crops.append((region, crop_path))
    return crops


def build_desktop_context(request: DesktopContextRequest) -> DesktopContextSnapshot:
    screenshot_path = _capture_display_frame()
    image_size = _get_image_size(screenshot_path)
    focus_regions, ocr_text = _collect_focus_regions(screenshot_path, image_size, request.include_ocr)
    terminal_log_excerpt = _read_terminal_excerpt(request.terminal_log_path, request.tail_lines)

    if screenshot_path:
        summary_parts = [
            analyze_visuals(screenshot_path, _profile_prompt(request.prompt, request.vision_profile))
        ]
        if request.use_focus_regions and focus_regions:
            focus_crops = _crop_focus_regions(screenshot_path, focus_regions)
            try:
                for region, crop_path in focus_crops:
                    crop_summary = analyze_visuals(
                        crop_path,
                        _profile_prompt(
                            f"{request.prompt}\nFocus region: {region.label} at "
                            f"({region.x},{region.y}) size {region.width}x{region.height}.",
                            "v2drop" if request.vision_profile != "bitvla" else request.vision_profile,
                        ),
                    )
                    summary_parts.append(f"[Focus:{region.label}] {crop_summary}")
            finally:
                for _, crop_path in focus_crops:
                    try:
                        os.unlink(crop_path)
                    except OSError:
                        pass
        visual_summary = "\n\n".join(part for part in summary_parts if part)
    else:
        visual_summary = "Desktop capture unavailable."

    return DesktopContextSnapshot(
        prompt=request.prompt,
        vision_profile=request.vision_profile,
        screenshot_path=screenshot_path,
        screen_size=image_size,
        visual_summary=visual_summary,
        ocr_text=ocr_text,
        terminal_log_excerpt=terminal_log_excerpt,
        focus_regions=focus_regions,
        engine_metadata={
            "vision_profile": request.vision_profile,
            "focus_region_count": len(focus_regions),
            "ocr_enabled": request.include_ocr,
            "ocr_available": easyocr is not None,
            "fastmcp_available": FastMCP is not None,
        },
    )


def execute_terminal_with_context(request: TerminalActionRequest) -> TerminalActionResult:
    from core_os.actions import terminal_executor

    before_context = None
    after_context = None
    prompt = request.prompt or f"Inspect the desktop and active logs before running: {request.command}"

    if request.capture_before:
        before_context = build_desktop_context(
            DesktopContextRequest(
                prompt=prompt,
                vision_profile=request.vision_profile,
                include_ocr=request.include_ocr,
                terminal_log_path=request.terminal_log_path,
                tail_lines=request.tail_lines,
            )
        )

    result = terminal_executor(request.command, cwd=request.cwd)

    if request.capture_after:
        after_context = build_desktop_context(
            DesktopContextRequest(
                prompt=f"Verify the desktop and active logs after running: {request.command}",
                vision_profile=request.vision_profile,
                include_ocr=request.include_ocr,
                terminal_log_path=request.terminal_log_path,
                tail_lines=request.tail_lines,
            )
        )

    return TerminalActionResult(
        command=request.command,
        cwd=request.cwd,
        returncode=int(result.get("returncode", 0)),
        stdout=result.get("stdout", ""),
        stderr=result.get("stderr", ""),
        before_context=before_context,
        after_context=after_context,
    )


def plan_agent_handoff(request: AgentHandoffRequest) -> AgentHandoffResult:
    steps = [
        AgentHandoffStep(
            agent="Milla-System-Admin",
            action="capture_context",
            summary="Capture desktop, OCR, and terminal-state context before deciding who should act.",
            payload={
                "vision_profile": request.vision_profile,
                "terminal_log_path": request.terminal_log_path,
            },
        )
    ]

    if request.command:
        steps.append(
            AgentHandoffStep(
                agent="Milla-System-Admin",
                action="run_command",
                summary="Execute the requested shell action with pre/post visual verification.",
                payload={"command": request.command, "cwd": request.cwd},
            )
        )

    delegate_summary = (
        "Translate runtime findings into code or config changes if the captured state shows a fix is needed."
        if request.command
        else "Turn the captured GUI/log state into concrete engineering actions and code edits."
    )
    steps.append(
        AgentHandoffStep(
            agent="Milla-Coder",
            action="synthesize_fix",
            summary=delegate_summary,
            payload={"objective": request.objective},
        )
    )

    execution = None
    if request.execute and request.command:
        execution = execute_terminal_with_context(
            TerminalActionRequest(
                command=request.command,
                cwd=request.cwd,
                vision_profile=request.vision_profile,
                terminal_log_path=request.terminal_log_path,
            )
        )

    final_summary = (
        "Handoff plan prepared. "
        "System-Admin owns visual/system grounding, and Coder owns the resulting implementation work."
    )
    if execution is not None:
        final_summary += f" Command executed with return code {execution.returncode}."

    return AgentHandoffResult(
        objective=request.objective,
        steps=steps,
        execution=execution,
        final_summary=final_summary,
    )


def list_control_mcp_tools() -> list[dict[str, str]]:
    return [
        {
            "name": "desktop_context_snapshot",
            "description": "Capture screenshot, OCR, focus regions, and optional terminal log context.",
        },
        {
            "name": "execute_terminal_with_context",
            "description": "Run a shell command with before/after desktop and log verification.",
        },
        {
            "name": "agent_handoff_plan",
            "description": "Build a typed handoff between Milla-System-Admin and Milla-Coder.",
        },
    ]


def invoke_control_mcp_tool(tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = arguments or {}
    if tool_name == "desktop_context_snapshot":
        return build_desktop_context(DesktopContextRequest(**payload)).model_dump()
    if tool_name == "execute_terminal_with_context":
        return execute_terminal_with_context(TerminalActionRequest(**payload)).model_dump()
    if tool_name == "agent_handoff_plan":
        return plan_agent_handoff(AgentHandoffRequest(**payload)).model_dump()
    raise ValueError(f"Unknown control MCP tool: {tool_name}")


def get_control_mcp_status() -> dict[str, Any]:
    return {
        "server_available": FastMCP is not None,
        "tool_count": len(list_control_mcp_tools()),
        "tools": list_control_mcp_tools(),
    }


def create_control_mcp_server():
    if FastMCP is None:
        raise RuntimeError("FastMCP is unavailable in the active Python environment.")

    mcp = FastMCP(
        name="milla-desktop-control",
        instructions=(
            "Secure desktop-control bridge for Milla-Rayne. "
            "Tools provide screenshot, OCR, terminal log context, and typed handoffs."
        ),
    )

    @mcp.tool(
        name="desktop_context_snapshot",
        description="Capture screenshot, OCR, focus regions, and optional terminal log context.",
    )
    def _desktop_context_snapshot(**kwargs):
        return build_desktop_context(DesktopContextRequest(**kwargs)).model_dump()

    @mcp.tool(
        name="execute_terminal_with_context",
        description="Run a shell command with before/after desktop and log verification.",
    )
    def _execute_terminal_with_context(**kwargs):
        return execute_terminal_with_context(TerminalActionRequest(**kwargs)).model_dump()

    @mcp.tool(
        name="agent_handoff_plan",
        description="Create a typed Milla-System-Admin to Milla-Coder handoff plan.",
    )
    def _agent_handoff_plan(**kwargs):
        return plan_agent_handoff(AgentHandoffRequest(**kwargs)).model_dump()

    return mcp


def run_control_mcp_server():
    create_control_mcp_server().run()


if __name__ == "__main__":
    run_control_mcp_server()
