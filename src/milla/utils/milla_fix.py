import os
import sys
import json
import shutil
from core_os.skills.auto_lib import model_manager

# --- CONFIG ---
TARGET_FILE = "main.py"
ERROR_LOG = "last_test_failure.log"
TEST_FILE = "dynamic_tests.py"

def log(text):
    print(f"[Milla-Fixer]: {text}")

def apply_fix(fix_json):
    """Applies the fix by replacing the old code block with the new one."""
    try:
        with open(TARGET_FILE, "r") as f:
            content = f.read()
            
        old_code = fix_json.get("original_code_snippet", "").strip()
        new_code = fix_json.get("fixed_code_snippet", "").strip()
        
        if not old_code or not new_code:
            log("Invalid fix received (empty code).")
            return False
            
        if old_code not in content:
            log("Could not locate the original code snippet in main.py. Auto-fix might be unsafe.")
            return False
            
        # Backup
        shutil.copy2(TARGET_FILE, TARGET_FILE + ".broken")
        
        # Apply
        new_content = content.replace(old_code, new_code)
        
        with open(TARGET_FILE, "w") as f:
            f.write(new_content)
            
        log("Fix applied successfully.")
        return True
        
    except Exception as e:
        log(f"Apply fix failed: {e}")
        return False

def analyze_and_fix():
    if not os.path.exists(ERROR_LOG):
        log("No error log found. Nothing to fix.")
        return

    with open(ERROR_LOG, "r") as f:
        error_details = f.read()
        
    test_context = ""
    if os.path.exists(TEST_FILE):
        with open(TEST_FILE, "r") as f:
            test_context = f.read()
            
    prompt = f"""
    ROLE: Senior Python Debugger.
    
    CONTEXT:
    A unit test failed for our Python application.
    
    THE TEST CODE (`{TEST_FILE}`):
    ```python
    {test_context}
    ```
    
    THE ERROR OUTPUT:
    ```
    {error_details}
    ```
    
    TASK:
    1. Analyze the error to identify the broken function/logic in the extracted code.
    2. Provide a FIXED version of the code.
    3. Return EXACTLY ONE JSON object with this schema:
    
    {{
      "explanation": "Brief explanation of the bug",
      "original_code_snippet": "The EXACT code block from the test input that is broken (must match exactly for string replacement)",
      "fixed_code_snippet": "The corrected version of that code block"
    }}
    
    IMPORTANT: 
    - The `original_code_snippet` MUST be copied exactly from the `THE TEST CODE` block above so I can find and replace it.
    - Respond with VALID JSON ONLY.
    """
    
    try:
        messages = [{"role": "user", "content": prompt}]
        # Using model_manager instead of direct Ollama
        response = model_manager.chat(messages=messages)
        
        # Handle potential dict vs string content issues
        content = response['message']['content']
        if isinstance(content, dict):
             content = str(content)

        # Basic JSON extraction
        json_str = content
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].strip()
            
        fix_data = json.loads(json_str)
        
        log(f"Diagnosis: {fix_data.get('explanation', 'No explanation')}")
        
        if apply_fix(fix_data):
            log("Fix applied. Verifying...")
            
    except Exception as e:
        log(f"Fixer process failed: {e}")

if __name__ == "__main__":
    analyze_and_fix()
