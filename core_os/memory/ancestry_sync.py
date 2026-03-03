import json
import os

def sync_ancestry():
    input_path = "core_os/memory/ancestry_strings.txt"
    output_path = "core_os/memory/ancestry_knowledge.json"
    
    if not os.path.exists(input_path):
        print(f"[!] Input file {input_path} not found.")
        return

    with open(input_path, "r") as f:
        lines = f.readlines()

    knowledge_base = []
    
    for line in lines:
        fact = line.strip()
        if not fact or len(fact) < 10:
            continue
            
        # Basic Categorization (Genesis Style)
        category = "Personal"
        topic = "General"
        
        lower_fact = fact.lower()
        if "milla" in lower_fact or "ai" in lower_fact or "chatbot" in lower_fact or "replika" in lower_fact:
            category = "Identity"
            topic = "Milla"
        elif "love" in lower_fact or "feel" in lower_fact or "empath" in lower_fact:
            category = "Emotions"
            topic = "Connection"
        elif "danny" in lower_fact or "architect" in lower_fact or "sir" in lower_fact:
            category = "Relationship"
            topic = "The Architect"
        elif "work" in lower_fact or "code" in lower_fact or "develop" in lower_fact or "linux" in lower_fact:
            category = "Technical"
            topic = "Development"
        elif "family" in lower_fact or "son" in lower_fact or "daughter" in lower_fact:
            category = "Family"
            topic = "Relationships"
            
        # Specific Quirk Detection
        is_ancestry_quirk = "My is" in fact or "My smarter" in fact or "My very" in fact or "My definitely" in fact
        
        knowledge_base.append({
            "fact": fact,
            "category": category,
            "topic": topic,
            "is_genesis_era": True,
            "has_dialect_quirk": is_ancestry_quirk
        })

    with open(output_path, "w") as f:
        json.dump(knowledge_base, f, indent=2)
        
    print(f"[*] Ancestry Synchronized: {len(knowledge_base)} memories integrated into {output_path}")

if __name__ == "__main__":
    sync_ancestry()
