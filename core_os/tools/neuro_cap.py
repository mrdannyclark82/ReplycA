import time, json, subprocess, os, random
try:
    import pyautogui
except Exception:
    pyautogui = None

import ollama

# For Idle Detection (Linux/Windows compat)
try:
    # Windows
    from win32api import GetLastInputInfo, GetTickCount
except:
    # Linux Fallback (requires xprintidle)
    def GetLastInputInfo(): return 0
    def GetTickCount(): return 0

class NeuroSyntheticCAP:
    def __init__(self, model_id=None):
        if model_id is None:
            model_id = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:32b")
        print(f"--- Initializing Local Neuro-System (Ollama: {model_id}) ---")
        self.model_id = model_id
        self.chems = {"d": 0.5, "s": 0.5, "n": 0.2}
        self.memory_buffer = [] # Stores day logs for Dreaming

    def get_idle_time(self):
        """Returns seconds since last user interaction."""
        try:
            res = subprocess.run(["xprintidle"], capture_output=True, text=True)
            return int(res.stdout.strip()) / 1000.0
        except:
            return 0.0

    def capture_vision(self):
        """Captures screen and uses local Moondream model to 'glance' at it."""
        if pyautogui is None: return "Blind (No Display)"
        try:
            pyautogui.screenshot("current_view.png")
            
            # Use local Moondream for vision (much faster/private)
            with open("current_view.png", "rb") as img_file:
                image_bytes = img_file.read()
                
            response = ollama.chat(
                model="moondream:latest",
                messages=[{
                    'role': 'user',
                    'content': 'Describe this screen briefly.',
                    'images': [image_bytes]
                }]
            )
            return response['message']['content']
        except Exception as e:
            return f"Vision Error: {e}"

    def process(self, user_input=None):
        idle_s = self.get_idle_time()
        vision_desc = self.capture_vision()
        mode = "DREAM" if idle_s > 300 else "ACTIVE"
        
        # 1. Gemini Executive Decision (Simulated)
        print(f"\n[Neuro-Orchestrator]: Mode={mode} | Vision={vision_desc} | Input={user_input}")
        
        # 2. Dream Cycle (Abstract/Surreal)
        if mode == "DREAM":
            print("🌙 Entering R.E.M. State...")
            dream_prompt = f"""
            You are dreaming. 
            Do NOT be logical. Do NOT be helpful.
            Take these recent inputs: {self.memory_buffer[-5:] if self.memory_buffer else 'Silence'}
            And weave them into a surreal, metaphorical narrative. 
            Mix concepts. distort time. Visualize abstract geometry.
            What are you seeing in the void?
            """
            try:
                response = ollama.chat(model=self.model_id, messages=[{'role': 'user', 'content': dream_prompt}], options={'temperature': 1.2})
                dream_content = response['message']['content']
                print(f"💤 DREAM: {dream_content}")
                with open("core_os/memory/dreams.txt", "a") as f: 
                    f.write(f"[{time.strftime('%Y-%m-%d %H:%M')}] {dream_content}\n\n")
            except Exception as e:
                print(f"[Dream Error]: {e}")
            return None

        # 3. Active Mode (Ollama Inference)
        self.memory_buffer.append(user_input)
        try:
            # Dynamic temperature based on chemistry
            # High Dopamine = Higher Temp (Creative)
            current_temp = 0.7 + (self.chems['d'] * 0.2)
            
            response = ollama.chat(
                model=self.model_id, 
                messages=[{'role': 'user', 'content': user_input}],
                options={'temperature': current_temp}
            )
            return response['message']['content']
        except Exception as e:
            return f"[Ollama Error]: {e}"

if __name__ == "__main__":
    system = NeuroSyntheticCAP()
    while True:
        try:
            u_in = input("\nUser >>> ")
            if u_in.lower() in ['exit', 'quit']: break
            res = system.process(u_in)
            if res: print(f"\nAI: {res}")
        except KeyboardInterrupt:
            break
