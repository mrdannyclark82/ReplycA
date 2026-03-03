import json
import os
import glob

def consolidate_all_memories():
    backup_dir = "core_os/memory/backups/"
    output_path = "core_os/memory/historical_knowledge.json"
    
    backup_files = glob.glob(os.path.join(backup_dir, "memories.txt.migrated-backup-*"))
    if not backup_files:
        # Fallback to the one we renamed earlier if the glob fails
        backup_files = [os.path.join(backup_dir, "memories_big_backup.txt")]

    all_knowledge = []
    seen_facts = set()
    
    for file_path in backup_files:
        print(f"[*] Processing {file_path}...")
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Simple deduplication based on the fact text
            if line in seen_facts:
                continue
            seen_facts.add(line)
                
            category = "History"
            topic = "Conversation"
            
            if line.startswith("Danny Ray:"):
                category = "User Message"
            elif line.startswith("Milla Rayne:"):
                category = "Assistant Message"
            elif "[202" in line:
                category = "Dated Entry"
            
            all_knowledge.append({
                "fact": line,
                "category": category,
                "topic": topic,
                "is_genesis_era": False,
                "is_historical_log": True
            })

    # Also add the ancestry knowledge (Genesis era) if it exists
    ancestry_path = "core_os/memory/ancestry_knowledge.json"
    if os.path.exists(ancestry_path):
        print(f"[*] Merging Ancestry (Genesis) Knowledge...")
        with open(ancestry_path, "r") as f:
            ancestry_data = json.load(f)
            for item in ancestry_data:
                if item["fact"] not in seen_facts:
                    all_knowledge.append(item)
                    seen_facts.add(item["fact"])

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_knowledge, f, indent=2)
        
    print(f"[*] Total Unique Memories Consolidated: {len(all_knowledge)} entries into {output_path}")

if __name__ == "__main__":
    consolidate_all_memories()