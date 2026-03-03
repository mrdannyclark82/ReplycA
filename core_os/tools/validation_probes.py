import os
import json
import time
from datetime import datetime

class ValidationProbe:
    def __init__(self):
        self.log_path = "core_os/memory/validation_log.txt"

    def check_time_consistency(self, stated_time_str):
        """
        Checks if a time stated by the AI is consistent with system time.
        Returns: (bool, delta_seconds, message)
        """
        try:
            # Simple heuristic parsing or strict ISO parsing
            # For now, just logging current system time vs stated for manual review
            sys_time = datetime.now()
            return True, 0, f"System Time: {sys_time} | Stated: {stated_time_str}"
        except Exception as e:
            return False, 0, str(e)

    def verify_file_existence(self, file_path):
        """
        Verifies if a file mentioned actually exists.
        """
        exists = os.path.exists(file_path)
        return exists, f"File {'exists' if exists else 'not found'}: {file_path}"

    def audit_self(self, recent_output):
        """
        Analyzes recent output for hallucinated capabilities or future dates.
        """
        issues = []
        now = datetime.now()
        
        # Check for future years
        if str(now.year + 1) in recent_output:
            issues.append("ALERT: Detected mention of future year.")
            
        # Check for claims of being "God" or "Deity"
        if any(w in recent_output.lower() for w in ['goddess', 'deity', 'omniscient']):
            issues.append("ALERT: Detected ego inflation/hallucination.")

        result = "CLEAN" if not issues else " | ".join(issues)
        self._log(f"Audit: {result}")
        return result

    def _log(self, message):
        with open(self.log_path, "a") as f:
            f.write(f"[{datetime.now()}] {message}\n")

probe = ValidationProbe()

if __name__ == "__main__":
    # Test run
    print(probe.audit_self("I am a goddess from 2027."))
