#!/usr/bin/env python3

import os
import sys
import subprocess
import readline

class EnhancedTerminal:
    def __init__(self):
        self.commands = {
            'help': self.show_help,
            'clear': self.clear_screen,
            'tree': self.show_tree,
            'project': self.project_info,
            'readme': self.create_readme,
            'setup': self.setup_info,
            'exit': self.exit_terminal
        }
        
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear')
        
    def show_help(self):
        """Display available commands"""
        print("""
Enhanced Terminal Commands:
  help     - Show this help message
  clear    - Clear the screen
  tree     - Show project structure
  project  - Show project information
  readme   - Generate/update README.md
  setup    - Show setup information
  exit     - Exit the enhanced terminal
        """)
        
    def show_tree(self):
        """Show project tree structure"""
        print("\n\033[1;34m=== Project Structure ===\033[0m")
        try:
            result = subprocess.run(['ls', '-la'], capture_output=True, text=True)
            print(result.stdout)
        except Exception as e:
            print(f"Error showing tree: {e}")
            
    def project_info(self):
        """Show project information"""
        print("\n\033[1;32mArch Regulator Agent\033[0m")
        print("An AI automation tool for Arch Linux systems")
        print("Features:")
        print("  • Terminal command execution")
        print("  • Persistent memory management")
        print("  • Dynamic tool generation")
        print("  • Safety mechanisms (Safe Word)")
        print("  • Web interface for Ollama integration")
        
    def create_readme(self):
        """Generate README.md file"""
        print("\nGenerating README.md...")
        try:
            with open("README.md", "w") as f:
                f.write("""# Arch Regulator Agent

## Description
A lean and stable AI automation tool designed specifically for Arch Linux systems.

## Features
- Terminal command execution
- Persistent memory management with SQLite
- Dynamic tool generation capabilities
- Safety mechanisms including emergency stop
- Web interface for Ollama integration

## Installation
1. Ensure you're on Arch Linux
2. Install Python 3.11+ and Ollama
3. Run: bash setup.sh

## Usage
1. Activate virtual environment: source venv/bin/activate
2. Run agent: python main.py
3. Emergency stop: Double-tap Spacebar

## Files
- main.py: Primary agent (stable)
- main1.py: Experimental agent with OCR
- setup.sh: Installation script
- index.html: Web interface
""")
            print("README.md created successfully!")
        except Exception as e:
            print(f"Error creating README.md: {e}")
            
    def setup_info(self):
        """Show setup information"""
        print("\n\033[1;33mSetup Information\033[0m")
        print("Main setup script: setup.sh")
        print("Requirements: requirements.txt")
        print("Python version: 3.11+")
        print("System: Arch Linux (uses pacman)")
        
    def exit_terminal(self):
        """Exit the enhanced terminal"""
        print("Exiting enhanced terminal...")
        sys.exit(0)
        
    def run(self):
        """Run the enhanced terminal"""
        self.clear_screen()
        print("\033[1;36m=== Enhanced Terminal for Arch Regulator Agent ===\033[0m")
        print("Type 'help' for available commands")
        
        while True:
            try:
                cmd = input("\n\033[1;32march-terminal>\033[0m ").strip().lower()
                
                if cmd in self.commands:
                    self.commands[cmd]()
                elif cmd:
                    # Execute as system command
                    try:
                        result = subprocess.run(cmd.split(), capture_output=True, text=True)
                        if result.stdout:
                            print(result.stdout)
                        if result.stderr:
                            print(f"Error: {result.stderr}")
                    except Exception as e:
                        print(f"Command error: {e}")
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except EOFError:
                print("\nExiting...")
                break

if __name__ == "__main__":
    terminal = EnhancedTerminal()
    terminal.run()
