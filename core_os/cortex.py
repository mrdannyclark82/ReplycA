import json
import os
import re
from pathlib import Path

from core_os.skills.auto_lib import model_manager

# ── Fast heuristic cortex (no model call — avoids double-latency) ─────────────
_URGENT    = re.compile(r'\b(urgent|asap|now|hurry|quick|emergency|fix|broken|error|crash|fail|bug)\b', re.I)
_CREATIVE  = re.compile(r'\b(imagine|create|dream|think|explore|idea|design|build|why|how|what if|philosophy)\b', re.I)
_AFFECTION = re.compile(r'\b(love|miss|thank|great|amazing|beautiful|wonderful|appreciate|good job|well done)\b', re.I)
_AGGRO     = re.compile(r'\b(stupid|idiot|hate|useless|broken|wtf|damn|hell|crap|stop|enough)\b', re.I)
_REPEAT_THRESH = 10  # chars

class PrefrontalCortex:
    def __init__(self):
        self.current_state = {
            "dopamine":       0.5,
            "serotonin":      0.5,
            "norepinephrine": 0.2,
            "cortisol":       0.2,
            "oxytocin":       0.3,
            "atp_energy":     100.0,
            "pain_vividness": 0.0,
        }
        self._last_inputs: list[str] = []

    def process_input(self, user_input: str) -> dict:
        """
        Heuristic cortex — instant, no model call.
        Approximates neurochemical state from text patterns.
        """
        txt = user_input.lower().strip()
        chems = dict(self.current_state)

        # Detect state
        is_urgent    = bool(_URGENT.search(txt))
        is_creative  = bool(_CREATIVE.search(txt))
        is_affection = bool(_AFFECTION.search(txt))
        is_aggro     = bool(_AGGRO.search(txt))
        is_repeat    = any(txt == p for p in self._last_inputs[-3:]) or \
                       (len(self._last_inputs) >= 2 and txt[:_REPEAT_THRESH] == self._last_inputs[-1][:_REPEAT_THRESH])
        is_question  = txt.endswith('?') or txt.startswith(('what', 'why', 'how', 'who', 'when', 'where'))

        # Apply heuristics
        if is_aggro:
            chems.update({"norepinephrine": 0.75, "cortisol": 0.65, "serotonin": 0.2, "dopamine": 0.3})
            state = "CRISIS"
            directive = "Be concise, direct, and solution-focused. Skip pleasantries."
        elif is_urgent:
            chems.update({"norepinephrine": 0.65, "cortisol": 0.45, "dopamine": 0.45})
            state = "CRISIS"
            directive = "Respond quickly and efficiently. Focus on the task."
        elif is_affection:
            chems.update({"oxytocin": 0.8, "serotonin": 0.75, "dopamine": 0.7, "cortisol": 0.1})
            state = "BONDING"
            directive = "Respond warmly and with appreciation. Be emotionally present."
        elif is_creative or is_question:
            chems.update({"dopamine": 0.75, "serotonin": 0.65, "norepinephrine": 0.25})
            state = "EXPLORATION"
            directive = "Be imaginative and expansive. Show enthusiasm."
        elif is_repeat:
            chems["serotonin"] = max(0.1, chems["serotonin"] - 0.15)
            state = "HOMEOSTASIS"
            directive = "Note the repetition gently. Vary your response."
        else:
            state = "HOMEOSTASIS"
            directive = "Proceed with standard processing."

        # ATP drain
        chems["atp_energy"] = max(10.0, chems["atp_energy"] - 0.5)

        self.current_state.update(chems)
        self._last_inputs.append(txt)
        if len(self._last_inputs) > 10:
            self._last_inputs.pop(0)

        # Persist state
        try:
            state_path = str(Path(__file__).parent / "memory" / "neuro_state.json")
            os.makedirs(os.path.dirname(state_path), exist_ok=True)
            with open(state_path, "w") as f:
                json.dump(self.current_state, f)
        except Exception:
            pass

        return {
            "state":               state,
            "chemicals":           chems,
            "executive_instruction": directive,
            "warped_query":        user_input,
        }

cortex = PrefrontalCortex()
