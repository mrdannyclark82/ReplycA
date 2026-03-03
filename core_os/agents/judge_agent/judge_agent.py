import os
import json
import sys
from datetime import datetime

# Shared utils
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import security_utils

DATA_DIR = security_utils.DATA_DIR
ANALYSIS_FILE = os.path.join(DATA_DIR, "analysis_report.json")
FLAGS_FILE = security_utils.FLAGS_FILE
REPORT_DIR = os.path.join(DATA_DIR, "reports")

def generate_verdict(analysis, flags):
    verdict = {
        "timestamp": datetime.now().isoformat(),
        "risk_level": "LOW",
        "who": "Unknown", # Would need user tracking
        "what": "System Anomaly Detection",
        "where": "Multiple Systems",
        "why": "Behavioral deviations detected",
        "when": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "actions": []
    }
    
    score = analysis.get("risk_score", 0)
    
    if score > 50:
        verdict["risk_level"] = "CRITICAL"
        verdict["actions"].append("IMMEDIATE INTERVENTION REQUIRED: Check processes and network immediately.")
        verdict["actions"].append("Consider isolating the host from network.")
    elif score > 20:
        verdict["risk_level"] = "HIGH"
        verdict["actions"].append("Investigate suspicious processes.")
        verdict["actions"].append("Review recent log entries for unauthorized access.")
    elif score > 10:
        verdict["risk_level"] = "MEDIUM"
        verdict["actions"].append("Monitor system logs closely.")
    else:
        verdict["risk_level"] = "LOW"
        verdict["actions"].append("Routine log review.")

    # Try to extract 'who' from flags (e.g., user in log)
    users_seen = set()
    for flag in flags:
        details = flag.get("details", "")
        if "user " in details:
            parts = details.split("user ")
            if len(parts) > 1:
                user = parts[1].split()[0]
                users_seen.add(user)
    
    if users_seen:
        verdict["who"] = ", ".join(users_seen)
        
    return verdict

def main():
    print("Running Judge Agent...")
    
    if not os.path.exists(ANALYSIS_FILE):
        print("No analysis to judge.")
        return

    try:
        with open(ANALYSIS_FILE, "r") as f:
            analysis = json.load(f)
            
        with open(FLAGS_FILE, "r") as f:
            flags = json.load(f)
            # Filter new flags
            new_flags = [f for f in flags if f.get("status") == "new"]

        verdict = generate_verdict(analysis, new_flags)
        
        # Save Report
        os.makedirs(REPORT_DIR, exist_ok=True)
        report_filename = f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path = os.path.join(REPORT_DIR, report_filename)
        
        with open(report_path, "w") as f:
            f.write(f"# Security Verdict Report\n")
            f.write(f"**Date:** {verdict['when']}\n")
            f.write(f"**Risk Level:** {verdict['risk_level']}\n\n")
            
            f.write(f"## Analysis (Who, What, Why, Where, When)\n")
            f.write(f"- **Who:** {verdict['who']}\n")
            f.write(f"- **What:** {verdict['what']}\n")
            f.write(f"- **Where:** {verdict['where']}\n")
            f.write(f"- **When:** {verdict['when']}\n")
            f.write(f"- **Why:** {verdict['why']}\n\n")
            
            f.write(f"## Suggested Actions\n")
            for action in verdict['actions']:
                f.write(f"- {action}\n")
                
            f.write(f"\n## Detailed Flags\n")
            for flag in new_flags:
                f.write(f"- [{flag.get('level', 'medium').upper()}] {flag.get('agent')}: {flag.get('details')}\n")
                
        print(f"Verdict: {verdict['risk_level']}")
        print(f"Report saved to: {report_path}")

        # Mark flags as processed
        for flag in flags:
            if flag.get("status") == "new":
                flag["status"] = "processed"
                
        with open(FLAGS_FILE, "w") as f:
            json.dump(flags, f, indent=4)

    except Exception as e:
        print(f"Judgment failed: {e}")

if __name__ == "__main__":
    main()
