"""
computer_use_agent.py — Grok-4 vision agentic loop for computer control.
Yields SSE-compatible dicts for each step.
"""
from __future__ import annotations
import json, time
from typing import Generator, Any

from core_os.skills.auto_lib import UnifiedModelManager
from core_os.skills.computer_use import take_screenshot, execute_action

MAX_STEPS  = 20
STEP_DELAY = 0.6  # seconds between screenshot and next action

SYSTEM_PROMPT = """You are Milla's Computer Use module. You control a Linux desktop.
You receive a screenshot and must decide ONE action to take toward the user's goal.

Respond ONLY with valid JSON — no markdown, no explanation outside the JSON.

Action schema (pick one):
{"action":"click",      "args":{"x":int,"y":int,"button":"left","double":false}, "reasoning":"..."}
{"action":"type",       "args":{"text":"string"},                                "reasoning":"..."}
{"action":"key",        "args":{"keys":["ctrl","c"]},                            "reasoning":"..."}
{"action":"scroll",     "args":{"x":int,"y":int,"delta":-3},                    "reasoning":"..."}
{"action":"move",       "args":{"x":int,"y":int},                                "reasoning":"..."}
{"action":"drag",       "args":{"dx":int,"dy":int,"duration":0.3},              "reasoning":"..."}
{"action":"shell",      "args":{"cmd":"bash command"},                           "reasoning":"..."}
{"action":"wait",       "args":{"seconds":1.0},                                  "reasoning":"..."}
{"action":"browser_goto",       "args":{"url":"https://..."},                   "reasoning":"..."}
{"action":"browser_click",      "args":{"selector":"css or text"},              "reasoning":"..."}
{"action":"browser_fill",       "args":{"selector":"input#q","text":"..."},     "reasoning":"..."}
{"action":"browser_text",       "args":{"selector":"body"},                     "reasoning":"..."}
{"action":"browser_screenshot", "args":{},                                      "reasoning":"..."}
{"action":"done",       "args":{"result":"what was accomplished"},              "reasoning":"task complete"}

Rules:
- Be precise with pixel coordinates — examine the screenshot carefully.
- Prefer shell/browser actions over GUI clicks when possible.
- If the goal is already achieved, return done immediately.
- Never loop the same action more than 3 times without progress.
"""


def run_agent(task: str, max_steps: int = MAX_STEPS) -> Generator[dict[str, Any], None, None]:
    """
    Generator — yields step dicts for SSE streaming:
    {"step": int, "action": str, "reasoning": str, "result": str, "screenshot": b64}
    On completion: {"step": n, "action": "done", "result": str, "done": true}
    On error:      {"error": str}
    """
    model_manager = UnifiedModelManager()
    history: list[dict] = []

    yield {"step": 0, "action": "start", "reasoning": f"Starting task: {task}", "result": "", "screenshot": ""}

    for step in range(1, max_steps + 1):
        try:
            # 1. Screenshot
            b64 = take_screenshot(scale=0.5)

            # 2. Build vision message
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                *history,
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64}"}
                        },
                        {
                            "type": "text",
                            "text": (
                                f"Task: {task}\n"
                                f"Step: {step}/{max_steps}\n"
                                f"Previous actions: {len(history)//2}\n"
                                "What is ONE action to take next? Reply with JSON only."
                            )
                        }
                    ]
                }
            ]

            # 3. Call vision model
            try:
                client = model_manager._get_client()
                resp   = client.chat.completions.create(
                    model=model_manager.default_model,
                    messages=messages,
                    max_tokens=256,
                    temperature=0.1,
                )
                raw = resp.choices[0].message.content.strip()
            except Exception as e:
                yield {"error": f"Vision API error: {e}"}
                return

            # 4. Parse action JSON
            try:
                # strip markdown fences if model wraps in them
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                action_dict = json.loads(raw)
            except Exception:
                yield {"error": f"Bad JSON from model: {raw[:200]}"}
                return

            reasoning = action_dict.get("reasoning", "")
            action_name = action_dict.get("action", "unknown")

            # 5. Execute action
            try:
                result = execute_action(action_dict)
            except Exception as e:
                result = f"execution error: {e}"

            # 6. Add to history for context
            history.append({"role": "assistant", "content": raw})
            history.append({
                "role": "user",
                "content": f"[Result of {action_name}]: {result}"
            })

            # Yield step event (include thumbnail screenshot)
            yield {
                "step":       step,
                "action":     action_name,
                "reasoning":  reasoning,
                "result":     result,
                "screenshot": b64,
            }

            # 7. Done?
            if action_name == "done":
                yield {"step": step, "action": "done", "result": result, "done": True, "screenshot": b64}
                return

            # 8. Keep history bounded
            if len(history) > 20:
                history = history[-20:]

            time.sleep(STEP_DELAY)

        except Exception as e:
            yield {"error": f"Agent step {step} error: {e}"}
            return

    yield {
        "step": max_steps,
        "action": "timeout",
        "result": f"Reached max steps ({max_steps}) without completing task.",
        "done": True,
        "screenshot": ""
    }
