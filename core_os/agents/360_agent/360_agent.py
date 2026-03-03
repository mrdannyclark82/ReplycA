import os
import json
import sys
from datetime import datetime

# Shared utils
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import security_utils

DATA_DIR = security_utils.DATA_DIR
FLAGS_FILE = security_utils.FLAGS_FILE
ANALYSIS_FILE = os.path.join(DATA_DIR, "analysis_report.json")

def analyze_flags(flags):
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "summary": "No critical threats detected.",
        "risk_score": 0,
        "correlated_events": [],
        "source_breakdown": {}
    }
    
    if not flags:
        return analysis

    # Breakdown by source
    for flag in flags:
        agent = flag.get("agent", "Unknown")
        analysis["source_breakdown"][agent] = analysis["source_breakdown"].get(agent, 0) + 1
        
    # Risk calculation (Simple heuristic)
    risk_score = 0
    weights = {"low": 1, "medium": 3, "high": 5, "critical": 10}
    
    for flag in flags:
        level = flag.get("level", "medium").lower()
        risk_score += weights.get(level, 3)
        
    analysis["risk_score"] = risk_score
    
    # Correlation Logic (Deep Seek Simulation)
    agents_involved = analysis["source_breakdown"].keys()
    if "Security Agent" in agents_involved and "Network Security Agent" in agents_involved:
        analysis["correlated_events"].append("High correlation: Process activity matches Network activity.")
        risk_score += 10 # Boost risk for correlated events
        
    if "Investigative Agent" in agents_involved and "Security Agent" in agents_involved:
        analysis["correlated_events"].append("High correlation: Log errors match Process activity.")
        risk_score += 10

    # Summary Generation
    if risk_score > 20:
        analysis["summary"] = "CRITICAL THREAT: Multiple high-risk indicators detected across agents."
    elif risk_score > 10:
        analysis["summary"] = "WARNING: Suspicious activity detected warranting investigation."
    else:
        analysis["summary"] = "NOTICE: Low-level anomalies detected."
        
    return analysis

def main():
    print("Running 360 Agent (Deep Seek Analysis)...")
    
    if not os.path.exists(FLAGS_FILE):
        print("No flags to analyze.")
        return

    try:
        with open(FLAGS_FILE, "r") as f:
            flags = json.load(f)
            
        # Filter only 'new' flags or analyze all?
        # Let's analyze all 'new' flags
        new_flags = [f for f in flags if f.get("status") == "new"]
        
        if not new_flags:
            print("No new flags to analyze.")
            return

        analysis = analyze_flags(new_flags)
        
        # Save analysis
        with open(ANALYSIS_FILE, "w") as f:
            json.dump(analysis, f, indent=4)
            
        print(f"Analysis complete. Risk Score: {analysis['risk_score']}")
        
        # Trigger Judge Agent
        next_agent = os.path.join(os.path.dirname(__file__), "../judge_agent/judge_agent.py")
        security_utils.trigger_next_agent(next_agent)
        
        # Mark flags as processed (optional, for now just keep them)
        
    except Exception as e:
        print(f"Analysis failed: {e}")

if __name__ == "__main__":
    main()
