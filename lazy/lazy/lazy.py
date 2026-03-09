import os
import re
import subprocess
from pathlib import Path

def extract_code_blocks(response):
    """Extract code blocks from markdown response"""
    pattern = r"```(\w+)\n(.*?)```"
    return re.findall(pattern, response, re.DOTALL)

def create_file(directory, filename, content):
    """Create file with content in specified directory"""
    filepath = Path(directory) / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Created: {filepath}")

def process_code_blocks(blocks):
    """Process extracted code blocks into categorized files"""
    html_content = ""
    css_content = ""
    js_content = ""
    python_content = ""
    
    for lang, code in blocks:
        if lang == "html":
            html_content += f"{code}\n"
        elif lang == "css":
            css_content += f"{code}\n"
        elif lang == "javascript":
            js_content += f"{code}\n"
        elif lang == "python":
            python_content += f"{code}\n"
        else:
            # Handle uncategorized code
            filename = f"misc_code.{lang}"
            create_file("output", filename, code)
    
    # Create categorized files
    if html_content:
        create_file("output", "index.html", html_content)
    if css_content:
        create_file("output/styles", "styles.css", css_content)
    if js_content:
        create_file("output/scripts", "script.js", js_content)
    if python_content:
        create_file("output", "main.py", python_content)

def get_current_model():
    """Get currently running Ollama model"""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        # Find the first model in the list (most recently used)
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        if lines:
            model_name = lines[0].split()[0]
            print(f"Using model: {model_name}")
            return model_name
        else:
            print("No models found, using default: llama2")
            return "llama2"
    except:
        print("Error detecting model, using default: llama2")
        return "llama2"

def run_ollama(prompt, model):
    """Execute Ollama command and return response"""
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Ollama error: {e}")
        return ""

def main():
    # Detect current model
    current_model = get_current_model()
    
    # Get user request
    user_prompt = input("Enter your coding request: ")
    
    # Add context for structured output
    full_prompt = (
        f"Create a complete solution for: {user_prompt}. "
        "Provide separate code blocks for different languages. "
        "Use proper markdown code block syntax with language identifiers."
    )
    
    # Get Ollama response
    print("Generating code...")
    response = run_ollama(full_prompt, current_model)
    
    if not response:
        print("Failed to get response from Ollama")
        return
    
    # Process response
    code_blocks = extract_code_blocks(response)
    process_code_blocks(code_blocks)
    
    print("\nCode generation complete! Files created in 'output' directory.")

if __name__ == "__main__":
    main()
