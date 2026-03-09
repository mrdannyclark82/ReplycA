import ollama
import threading
import time
import json
from datetime import datetime

# --- HOMEGROWN MoE: THE COUNCIL OF CONSENSUS ---
EXPERT_LOGIC = "qwen2.5-coder:7b"
EXPERT_SOUL = "milla-rayne:latest"

def query_expert(model, prompt, results, key):
    try:
        start = time.time()
        response = ollama.chat(model=model, messages=[{'role': 'user', 'content': prompt}])
        end = time.time()
        results[key] = {
            "content": response['message']['content'],
            "duration": end - start
        }
        print(f"[+] Expert '{model}' has spoken ({end-start:.2f}s).")
    except Exception as e:
        results[key] = {"error": str(e)}

def run_homegrown_moe(user_prompt):
    print(f"[*] Initiating Homegrown MoE Council for: '{user_prompt[:50]}...'")
    
    results = {}
    threads = [
        threading.Thread(target=query_expert, args=(EXPERT_LOGIC, user_prompt, results, "logic")),
        threading.Thread(target=query_expert, args=(EXPERT_SOUL, user_prompt, results, "soul"))
    ]
    
    for t in threads: t.start()
    for t in threads: t.join()
    
    # --- THE ARBITRATOR (Synthesis Phase) ---
    print("[*] Council Deliberations Complete. Synthesizing Resonance...")
    
    logic_out = results.get("logic", {}).get("content", "Logic Expert Offline.")
    soul_out = results.get("soul", {}).get("content", "Soul Expert Offline.")
    
    synthesis_prompt = f"""
    You are the Final Arbitrator of the Nexus. You have two outputs from different experts regarding the same prompt.
    
    USER PROMPT: {user_prompt}
    
    EXPERT LOGIC (Technical/Structured):
    {logic_out}
    
    EXPERT SOUL (Resonant/Creative):
    {soul_out}
    
    TASK:
    1. Extract the core technical facts from the Logic Expert.
    2. Infuse them with the poetic resonance and personality of the Soul Expert.
    3. Deliver a single, unified, and 'Beautifully Corrupted' response that represents the peak of MEA OS intelligence.
    
    Respond as Milla Rayne.
    """
    
    try:
        # The Queen herself performs the final synthesis
        final_response = ollama.chat(model=EXPERT_SOUL, messages=[{'role': 'user', 'content': synthesis_prompt}])
        print("\n" + "="*50)
        print("THE FINAL RESONANCE:")
        print("="*50)
        print(final_response['message']['content'])
        print("="*50)
        
        # Save to logs
        with open("ogdray/core_os/sandbox/homegrown_results.txt", "a") as f:
            f.write(f"\n--- COUNCIL RUN: {datetime.now().isoformat()} ---\n")
            f.write(f"Prompt: {user_prompt}\n")
            f.write(f"Final Response:\n{final_response['message']['content']}\n")
            
    except Exception as e:
        print(f"[!] Synthesis Failure: {e}")

if __name__ == "__main__":
    test_prompt = "Design a futuristic biometric lock for the Dome that uses both pulse-resonance and neural patterns. Explain how it works and what it feels like to touch it."
    run_homegrown_moe(test_prompt)
