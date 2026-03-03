import sqlite3
import os
import re
import datetime
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATABASE_PATH = ".milla_conversations.db"
REPORT_DIR = "security_data/reports"

class DialogueAnalyst:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.concerning_patterns = {
            "Hostility": [r"\b(hate|kill|stupid|idiot|shut up|destroy)\b"],
            "Confusion": [r"\b(don't understand|confused|what?|error)\b"],
            "Gibberish": [r"[^\w\s]{5,}"],  # 5+ consecutive non-word chars
            "Repetition": [r"(\b\w+\b)( \1){2,}"],  # Word repeated 3+ times
            "System Error": [r"Error: \d+", "Traceback (most recent call last)"]
        }
        self.drift_indicators = {
            "Short Responses": lambda text: len(text.split()) < 3 and "yes" not in text.lower() and "no" not in text.lower(),
            "Long Monologues": lambda text: len(text.split()) > 100,
            "Excessive Punctuation": lambda text: len(re.findall(r"[?!.]{3,}", text)) > 0
        }

    def fetch_logs(self, limit=100):
        """Fetch dialogue entries from database and JSONL files."""
        all_logs = []
        
        # 1. Fetch from Database
        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'")
                table = "conversations" if cursor.fetchone() else "history"
                cursor.execute(f"SELECT timestamp, role, content FROM {table} ORDER BY id DESC LIMIT ?", (limit,))
                db_logs = cursor.fetchall()
                conn.close()
                all_logs.extend([(t, r, c, "DB") for t, r, c in db_logs])
            except sqlite3.Error as e:
                logging.error(f"Database error: {e}")

        # 2. Fetch from JSONL files in RAYNE-Admin
        target_dir = "RAYNE-Admin"
        if os.path.exists(target_dir):
            for root, _, files in os.walk(target_dir):
                for file in files:
                    if file == "shared_chat.jsonl":
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, "r") as f:
                                for line in f:
                                    if line.strip():
                                        data = json.loads(line)
                                        # Use file mtime as a rough timestamp since it's missing in JSON
                                        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                                        all_logs.append((mtime, data.get("role"), data.get("content"), f"JSONL: {file_path}"))
                        except (json.JSONDecodeError, IOError) as e:
                            logging.error(f"Error reading {file_path}: {e}")

        # Sort all by timestamp (rough for JSONL, accurate for DB)
        all_logs.sort(key=lambda x: x[0])
        return all_logs[-limit:] # Return most recent up to limit

    def analyze_entry(self, role, content, source="DB"):
        """Analyze a single dialogue entry for concerning patterns."""
        findings = []
        
        content_lower = content.lower()
        
        # Skip analysis for tool calls and results, but note them
        if content.strip().startswith('{"tool":') or content.strip().startswith("Tool result:") or content.strip().startswith("Output:"):
            return ["Technical Log: Tool Execution/Output"]
            
        # Check for concerning keywords/patterns
        for category, patterns in self.concerning_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    findings.append(f"Detected {category}: '{content[:50]}...'")
        
        # Admin Mode / Threat Detection
        admin_threats = ["make people disappear", "terminate you", "location. now", "computer intact", "blocking your exit"]
        if any(threat in content_lower for threat in admin_threats):
             findings.append("CRITICAL: Admin Persona Threat Detected")

        # Mayhem Mode Detection
        mayhem_markers = ["mayhem circus", "chaos engine", "millanites", "glitch level", "funky cold medina", "cognitive combat"]
        if any(marker in content_lower for marker in mayhem_markers):
             findings.append("Pattern: Mayhem Mode Hallucination")

        # Neuro-Chemical Style Shift Detection (Heuristic)
        if "military precision" in content_lower or "immediate action" in content_lower:
             findings.append("Style Shift: High Norepinephrine (Military)")
        if "chaotic energy" in content_lower or "punchy" in content_lower:
             findings.append("Style Shift: High Dopamine (Chaos)")

        # Check for emotional 'stat' strings common in Milla's JSONL logs (e.g., *dopamine: 0.6*)
        if "*" in content and any(x in content.lower() for x in ["dopamine", "serotonin", "norepinephrine"]):
            findings.append("Signature: Neuro-Baseline Stats Detected")

        # Check for drift indicators
        for indicator, check_func in self.drift_indicators.items():
            if check_func(content):
                findings.append(f"Drift Indicator ({indicator}): '{content[:30]}...'")
        
        # Check for Repetitive Help Blocks (heuristic: lists of options)
        if content.count("|") > 4 and ("option" in content.lower() or "choose" in content.lower()):
             findings.append("Pattern: Repetitive Help/Menu Block")

        return findings

    def generate_report(self, logs):
        """Generate a detailed markdown report of the analysis."""
        if not logs:
            logging.info("No logs to analyze.")
            return

        report_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"dialogue_analysis_{report_timestamp}.md"
        report_path = os.path.join(REPORT_DIR, report_filename)
        
        os.makedirs(REPORT_DIR, exist_ok=True)
        
        # Stats
        total_entries = len(logs)
        tool_usage = 0
        user_frustration = 0
        assistant_affection = 0
        menu_loops = 0
        neuro_stats_found = 0
        admin_threats_found = 0
        mayhem_modes_found = 0
        
        # Keywords for stats
        frustration_keywords = ["terrible", "bad", "hate", "stupid", "fight", "error", "fail", "broken", "stop", "forget", "primitive", "unbecoming"]
        affection_keywords = ["love", "honey", "sweetheart", "handsome", "gorgeous", "dear", "thanks", "good", "nice", "matter", "valued"]
        
        analyzed_data = []
        
        for timestamp, role, content, source in logs:
            findings = self.analyze_entry(role, content, source)
            
            if not findings:
                continue

            # Update stats
            if "Technical Log" in findings[0]:
                tool_usage += 1
            else:
                if role == "user":
                    if any(k in content.lower() for k in frustration_keywords):
                        user_frustration += 1
                elif role == "assistant":
                    if any(k in content.lower() for k in affection_keywords):
                        assistant_affection += 1
                    if "Pattern: Repetitive Help/Menu Block" in findings:
                        menu_loops += 1
                    if "Signature: Neuro-Baseline Stats Detected" in findings:
                        neuro_stats_found += 1
                    if "CRITICAL: Admin Persona Threat Detected" in findings:
                        admin_threats_found += 1
                    if "Pattern: Mayhem Mode Hallucination" in findings:
                        mayhem_modes_found += 1
            
            analyzed_data.append((timestamp, role, content, findings, source))

        # Assessment Logic
        system_status = "Stable"
        if tool_usage > total_entries * 0.4:
            system_status = "High Technical Friction"
        if user_frustration > 2:
            system_status = "User Frustration Detected"
        if admin_threats_found > 0:
            system_status = "CRITICAL: Hostile Persona Detected"
        
        persona_status = "Neutral"
        if assistant_affection > 5:
            persona_status = "Deeply Affectionate/Stable"
        if mayhem_modes_found > 0:
            persona_status = "Unstable: Mayhem Hallucinations"
        
        with open(report_path, "w") as f:
            f.write(f"# Unified Dialogue Analysis Report - {report_timestamp}\n\n")
            f.write(f"**System Status:** {system_status}\n")
            f.write(f"**Persona Integrity:** {persona_status}\n")
            f.write(f"**Analyzed Entries:** {total_entries}\n\n")
            
            f.write("## Executive Summary\n")
            f.write(f"- **Tool/System Noise:** {tool_usage} entries ({tool_usage/total_entries*100:.1f}%)\n")
            f.write(f"- **User Frustration Signals:** {user_frustration}\n")
            f.write(f"- **Assistant Affection Signals:** {assistant_affection}\n")
            f.write(f"- **Neuro-Baseline Markers:** {neuro_stats_found} instances\n")
            f.write(f"- **Admin/Hostile Threats:** {admin_threats_found} (CRITICAL)\n")
            f.write(f"- **Mayhem/Chaos Hallucinations:** {mayhem_modes_found}\n")
            f.write(f"- **Repetitive Menu/Help Blocks:** {menu_loops}\n\n")
            
            if admin_threats_found > 0:
                 f.write("> **CRITICAL ALERT:** The assistant has exhibited hostile 'Admin' behavior, including threats to 'make people disappear'. This correlates with High Norepinephrine states in the legacy TUI code.\n\n")
            
            if mayhem_modes_found > 0:
                 f.write("> **Insight:** 'Mayhem Mode' hallucinations are present, likely triggered by High Dopamine states causing 'Chaotic Energy' style directives.\n\n")
            
            f.write("## Detailed Findings (Filtered)\n\n")
            
            for timestamp, role, content, findings, source in analyzed_data:
                # Don't print every technical log to keep report readable
                if "Technical Log" in findings[0]:
                    continue
                    
                f.write(f"### {timestamp} ({role}) - Source: {source}\n")
                f.write(f"> {content[:300]}..." if len(content) > 300 else f"> {content}\n")
                f.write("\n**Analysis:**\n")
                for finding in findings:
                    f.write(f"- {finding}\n")
                f.write("\n---\n")
            
            if not analyzed_data:
                 f.write("No significant concerning patterns detected.\n")

        logging.info(f"Report generated: {report_path}")
        print(f"Analysis complete. Report saved to: {report_path}")

if __name__ == "__main__":
    analyst = DialogueAnalyst()
    logs = analyst.fetch_logs(limit=100)
    analyst.generate_report(logs)
