import os
import re
import sys
import json
import subprocess
from core_os.skills.auto_lib import model_manager

# --- CONFIG ---
TARGET_FILE = "main.py"
TEST_FILE = "dynamic_tests.py"

def log(text):
    print(f"[Milla-QA]: {text}")

def extract_recent_features(sources, n=2):
    """
    Extracts the code of the last n auto-generated features.
    sources: single filepath (str) or list of filepaths/directories.
    """
    all_matches = []
    
    if isinstance(sources, str):
        sources = [sources]
        
    files_to_scan = []
    for src in sources:
        if os.path.isdir(src):
            for root, dirs, files in os.walk(src):
                for file in files:
                    if file.endswith(".py"):
                        files_to_scan.append(os.path.join(root, file))
        elif os.path.exists(src):
            files_to_scan.append(src)
            
    # Regex to find blocks. Matches: # --- AUTO-GENERATED FEATURE: Name ---\n# Reasoning: ...\n[Code]\n# ------------------
    pattern = re.compile(r"""(# --- AUTO-GENERATED FEATURE:.*?# -----------------------------------------------------)""", re.DOTALL)
    
    for filepath in files_to_scan:
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # If it's a dynamic tool (standalone file), treat whole file as feature
            if "dynamic_tools" in filepath and filepath.endswith(".py"):
                # Add a wrapper so LLM understands context
                feature_block = f"# --- DYNAMIC TOOL: {os.path.basename(filepath)} ---\n{content}\n# -----------------------------------------------------"
                all_matches.append(feature_block)
            else:
                matches = pattern.findall(content)
                all_matches.extend(matches)
        except Exception as e:
            log(f"Error reading {filepath}: {e}")
    
    # Return the last n matches found across all files
    return all_matches[-n:] if all_matches else []

def generate_tests(features):
    """Asks AI to write unit tests for the extracted features."""
    if not features:
        log("No features found to test.")
        return False

    features_code = "\n\n".join(features)
    
    prompt = f"""
    ROLE: QA Automation Engineer.
    
    CONTEXT:
    I have a Python application. Here are the most recent features added to it:
    
    ```python
    {features_code}
    ```
    
    TASK:
    1. Write a standalone Python `unittest` script to verify these specific features.
    2. Mock any external dependencies (like `pyautogui`, `pyttsx3`, `ollama`, `speech_recognition`, `requests`) using `unittest.mock`.
    3. The tests must run safely without UI or Hardware interaction (headless).
    4. Output ONLY the raw Python code for the test script. No markdown, no comments.
    
    STRATEGY:
    Include the feature code DIRECTLY in your test script (copy-paste) or mock the imports if they are external.
    Prioritize testing the LOGIC of the provided snippets.
    """
    
    try:
        messages = [{"role": "user", "content": prompt}]
        response = model_manager.chat(messages=messages)
        
        content = response['message']['content']
        if isinstance(content, dict):
            content = str(content)
            
        test_code = content
        
        # Cleanup markdown
        if "```python" in test_code:
            test_code = test_code.split("```python")[1].split("```")[0]
        elif "```" in test_code:
            test_code = test_code.split("```")[1].split("```")[0]
            
        with open(TEST_FILE, "w") as f:
            f.write(test_code.strip())
            
        return True
        
    except Exception as e:
        log(f"Test generation error: {e}")
        return False

def run_tests():
    log("Running dynamic tests...")
    result = subprocess.run([sys.executable, TEST_FILE], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    
    if result.returncode == 0:
        log("Tests PASSED.")
        # Clean up
        if os.path.exists(TEST_FILE):
            os.remove(TEST_FILE)
        return True
    else:
        log("Tests FAILED.")
        # Save error log for the fixer
        with open("last_test_failure.log", "w") as f:
            f.write(result.stderr + "\n" + result.stdout)
        return False

def main():
    log("Scanning for recent updates...")
    scan_targets = [TARGET_FILE, "core_os/dynamic_tools"]
    recent_features = extract_recent_features(scan_targets)
    
    if not recent_features:
        log("No features found in main.py or dynamic_tools to test.")
        sys.exit(0)
        
    log(f"Found {len(recent_features)} recent features.")
    
    if generate_tests(recent_features):
        success = run_tests()
        if not success:
            sys.exit(1) # Trigger Fixer
    else:
        log("Could not generate tests.")
        sys.exit(1) # Trigger Fixer (fallback)

if __name__ == "__main__":
    main()
