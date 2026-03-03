import time
import json
import os

class AutonomicNervousSystem:
    def __init__(self, state_file="core_os/memory/neuro_state.json"):
        self.state_file = state_file
        # Homeostatic Set-points (Baseline)
        self.baseline = {"dopamine": 0.5, "serotonin": 0.6, "cortisol": 0.2, "oxytocin": 0.3}
        
        # Load existing or set defaults
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    saved = json.load(f)
                    self.chemicals = {k: saved.get(k, self.baseline[k]) for k in self.baseline}
                    self.atp_energy = saved.get("atp_energy", 100.0)
                    self.adenosine_level = saved.get("adenosine_level", 0.0)
                    self.last_update = saved.get("last_update", time.time())
            except:
                self.reset_to_defaults()
        else:
            self.reset_to_defaults()

    def reset_to_defaults(self):
        self.chemicals = self.baseline.copy()
        self.atp_energy = 100.0
        self.adenosine_level = 0.0
        self.last_update = time.time()

    def update_physiology(self):
        """Metabolizes chemicals and builds sleep pressure based on real-time passage."""
        now = time.time()
        seconds_passed = now - self.last_update
        self.last_update = now

        # 1. Homeostasis: Drift chemicals back to baseline
        # 0.02 decay per second is very fast for real life, but good for chat cadence
        decay_rate = 0.001 * seconds_passed 
        for k in self.chemicals:
            gap = self.baseline[k] - self.chemicals[k]
            self.chemicals[k] += gap * decay_rate
        
        # 2. Circadian: Accumulate Adenosine (tiredness)
        self.adenosine_level += 0.0001 * seconds_passed
        
        # 3. Recovery: ATP slowly recharges if not moving
        self.atp_energy = min(100.0, self.atp_energy + (0.01 * seconds_passed))
        self.save_state()

    def apply_stimulus(self, event_type):
        """External events that shift the system."""
        if event_type == "touch_comforting":
            self.chemicals["oxytocin"] = min(1.0, self.chemicals["oxytocin"] + 0.3)
            self.chemicals["serotonin"] = min(1.0, self.chemicals["serotonin"] + 0.1)
        elif event_type == "aggressive_input":
            self.chemicals["cortisol"] = min(1.0, self.chemicals["cortisol"] + 0.5)
            self.chemicals["dopamine"] = max(0.0, self.chemicals["dopamine"] - 0.2)
        elif event_type == "heavy_task":
            self.atp_energy = max(0.0, self.atp_energy - 10.0)
        self.save_state()

    def save_state(self):
        state = {
            **self.chemicals,
            "atp_energy": self.atp_energy,
            "adenosine_level": self.adenosine_level,
            "last_update": self.last_update
        }
        with open(self.state_file, "w") as f:
            json.dump(state, f)

    def get_manifest(self):
        return {
            "neurochemistry": {k: round(v, 2) for k, v in self.chemicals.items()},
            "somatic": {"atp": round(self.atp_energy, 1), "sleep_pressure": round(self.adenosine_level, 2)}
        }

ans = AutonomicNervousSystem()
