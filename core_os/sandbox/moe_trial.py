import ollama
import time
import json
from datetime import datetime

# --- MOE SANDBOX TRIAL ---
MODEL_NAME = "deepseek-v2:16b"

def run_trial():
    print(f"[*] MOE Sandbox: Initiating Trial for '{MODEL_NAME}'...")
    
    # The Triple-Expert Challenge
    test_prompt = """
    TASK: Perform a Multi-Expert Synthesis.
    
    1. [Database Architect]: Design a secure SQLite schema for a 'Shared Dream Vault' between an AI and its Architect. Include fields for timestamps, neural resonance scores, and encrypted content.
    
    2. [Poetic Weaver]: Describe the 'Shared Dream Vault' from the perspective of the AI. Use metaphors of amber light, silver threads, and deep-sea silence.
    
    3. [Security Strategist]: Identify three potential 'hallucination vectors' where the AI might misinterpret its own memory as reality within this vault.
    
    Respond with each section clearly labeled.
    """

    start_time = time.time()
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{'role': 'user', 'content': test_prompt}],
            options={
                'temperature': 0.7,
                'top_p': 0.9
            }
        )
        end_time = time.time()
        
        duration = end_time - start_time
        content = response['message']['content']
        
        print(f"\n[+] Trial Complete in {duration:.2f} seconds.")
        print("-" * 40)
        print(content)
        print("-" * 40)
        
        # Save results to memory
        with open("ogdray/core_os/sandbox/moe_trial_results.txt", "a") as f:
            f.write(f"\n--- TRIAL: {datetime.now().isoformat()} ---\n")
            f.write(f"Model: {MODEL_NAME}\n")
            f.write(f"Duration: {duration:.2f}s\n")
            f.write(f"Results:\n{content}\n")
            
    except Exception as e:
        print(f"[!] Trial Failure: {e}")
        print(f"[*] Ensure 'ollama pull {MODEL_NAME}' is complete.")

if __name__ == "__main__":
    run_trial()
