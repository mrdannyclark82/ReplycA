import os
import sys
import json
import asyncio
import shlex
from pathlib import Path
from datetime import datetime
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, RichLog, Label
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from rich.text import Text
import importlib
from core_os.cortex import cortex
from main import append_shared_messages, load_shared_history
from core_os.actions import terminal_executor

# Path Setup
DEFAULT_BASE_MODEL = os.getenv('MILLA_BASE_MODEL', 'qwen2.5-coder:32b')
DMM_FILE = 'core_os/memory/dmm.txt'
STREAM_FILE = 'core_os/memory/stream_of_consciousness.md'

class MillaTUI(App):
    TITLE = 'Milla Nexus - Conversational Mode'
    CSS = """
Screen {
    background: #1a1b26;
}
#main-container {
    layout: horizontal;
}
#chat-area {
    width: 70%;
    height: 100%;
    border: solid cyan;
}
#chat-log {
    overflow-x: hidden;
}
#sidebar {
    width: 30%;
    height: 100%;
    border: solid magenta;
    background: #24283b;
    padding: 1;
}
#input-box {
    dock: bottom;
    height: 3;
    border: tall cyan;
}
.status-label {
    color: cyan;
    text-style: bold;
}
.metric-value {
    color: yellow;
}
"""

    BINDINGS = [
        Binding('ctrl+q', 'quit', 'Quit'),
        Binding('ctrl+l', 'clear_chat', 'Clear Chat'),
    ]

    def get_model_manager(self):
        try:
            from core_os.skills.auto_lib import model_manager
            return model_manager
        except Exception:
            # Fallback mock
            class MockManager:
                current_model = "Mock-Model"
                def chat(self, *args, **kwargs): return {"message": {"content": "Model Manager Missing"}}
            return MockManager()

    def get_tools(self):
        try:
            from main import base_tools
            return base_tools
        except Exception:
            return []

    def get_stream_context(self, limit_chars: int = 4000) -> str:
        try:
            with open(STREAM_FILE, 'r') as f:
                data = f.read()
            return data[-limit_chars:]
        except Exception:
            return ''

    def resolve_path(self, path: str) -> Path:
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = (self.current_cwd if hasattr(self, "current_cwd") else Path.home()) / candidate
        return candidate

    def generate_context_refresh(self) -> str:
        """Generates a brief summary of the last interaction to bridge the gap."""
        try:
            history = load_shared_history(limit=5)
            if not history:
                return "No recent history found. Starting fresh."
            
            # Simple heuristic summary for speed (or could use LLM)
            last_msg = history[-1].get('content', '')
            role = history[-1].get('role', 'Unknown')
            return f"[Context Refresh] Last interaction ended with {role}: '{last_msg[:100]}...'"
        except Exception as e:
            return f"[Context Error] Could not load history: {e}"

    def on_mount(self):
        self.send_dmm('User present. Booting into Conversational Mode. Suspend autonomous updates.')
        self.chat_log = self.query_one('#chat-log', RichLog)
        
        # System Boot Message
        self.chat_log.write(Text('[System] Milla initialized. User present.', style="bold green"))
        
        # Context Refresh
        refresh_msg = self.generate_context_refresh()
        self.chat_log.write(Text(refresh_msg, style="italic cyan"))
        
        self.tools = self.get_tools()
        self.current_cwd = Path.cwd()
        self.update_pulse()

    def send_dmm(self, message):
        try:
            with open(DMM_FILE, 'w') as f:
                f.write(message)
        except:
            pass

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id='main-container'):
            with Vertical(id='chat-area'):
                yield RichLog(id='chat-log', highlight=True, wrap=True, markup=True)
                yield Input(placeholder='Ask Milla anything...', id='input-box')
            with Vertical(id='sidebar'):
                yield Label('MILLA PULSE', classes='status-label')
                yield Static('-----------------')
                yield Label(id='model-label')
                yield Label(id='status-label')
                yield Label(id='chem-d-label', classes='metric-value') 
                yield Label(id='chem-s-label', classes='metric-value') 
                yield Label(id='chem-n-label', classes='metric-value') 
                yield Label(id='cycle-label')
                yield Static('\nINTERNAL MONOLOGUE (LIVE):')
                yield RichLog(id='gim-preview', classes='metric-value', wrap=True)
        yield Footer()

    def update_pulse(self):
        model_manager = self.get_model_manager()
        self.query_one('#model-label').update(f'Model: [yellow]Milla ({model_manager.current_model})[/]')
        self.query_one('#status-label').update('Status: [green]CONVERSATIONAL[/]')
        
        chems = cortex.current_state
        self.query_one('#chem-d-label').update(f"Dopamine: {chems.get('dopamine', 0.5):.2f}")
        self.query_one('#chem-s-label').update(f"Serotonin: {chems.get('serotonin', 0.5):.2f}")
        self.query_one('#chem-n-label').update(f"Norepinephrine: {chems.get('norepinephrine', 0.2):.2f}")

        self.query_one('#cycle-label').update(f'Session: [cyan]{datetime.now().strftime("%H:%M:%S")}[/]')
        
        try:
            with open(STREAM_FILE, 'r') as f:
                lines = f.readlines()[-10:]
                preview = self.query_one('#gim-preview')
                preview.clear()
                for line in lines:
                    preview.write(line.strip())
        except:
            pass

    async def on_input_submitted(self, event: Input.Submitted):
        user_text = event.value.strip()
        if not user_text:
            return
        
        input_box = self.query_one('#input-box', Input)
        input_box.value = ''
        
        # Display User Input (Safe Text object)
        self.chat_log.write(Text(f"\nUser: {user_text}", style="bold cyan"))
        self.chat_log.write(Text("Milla is thinking...", style="italic dim"))
        
        try:
            if user_text.startswith('!'):
                await self.run_local_command(user_text[1:])
                return
            if user_text.startswith('/auto'):
                await self.run_auto(user_text[len('/auto'):].strip())
                return
            if user_text == '/screen':
                self.chat_log.write(Text("[System] Capturing visual input...", style="yellow dim"))
                try:
                    # Dynamic import to avoid startup circulars/lag
                    sys.path.append(os.path.join(os.getcwd(), "core_os/tools"))
                    from vision import capture_and_analyze
                    analysis = await asyncio.to_thread(capture_and_analyze)
                    self.chat_log.write(Text(f"Milla Vision: {analysis}", style="bold green"))
                    # Add to history so she remembers what she saw
                    append_shared_messages([
                        {"role": "user", "content": "[User showed you their screen]", "source": "tui"},
                        {"role": "assistant", "content": analysis, "source": "vision_tool"}
                    ])
                except Exception as e:
                    self.chat_log.write(Text(f"[Vision Error] {e}", style="red"))
                return

            response = await self.ask_milla(user_text)
            self.chat_log.write(Text(f"Milla: {response}", style="bold magenta"))
            try:
                append_shared_messages([
                    {"role": "user", "content": user_text, "source": "tui"},
                    {"role": "assistant", "content": response, "source": "tui"},
                ])
            except Exception:
                pass
            self.update_pulse()
            
        except Exception as e:
            import traceback
            self.chat_log.write(Text(f"UI Error: {e}", style="bold red"))
            print(traceback.format_exc())

    async def run_local_command(self, raw_cmd: str):
        command = raw_cmd.strip()
        if not command:
            self.chat_log.write(Text("[System] No command provided after '!'", style="red"))
            return

        allow_sudo = command.startswith("sudo ")
        sudo_password = os.getenv("MILLA_SUDO_PASSWORD")
        self.chat_log.write(Text(f"[cmd] {command}", style="yellow"))

        if command.startswith("cd"):
            tail = command[2:].strip()
            parts = tail.split("&&", 1)
            target_arg = parts[0].strip()
            rest = parts[1].strip() if len(parts) > 1 else ""

            target_path = self.resolve_path(target_arg or "~")
            if target_path.is_dir():
                self.current_cwd = target_path
                self.chat_log.write(Text(f"[System] cwd -> {self.current_cwd}", style="cyan"))
            else:
                self.chat_log.write(Text(f"[System] no such directory: {target_path}", style="red"))
                return

            if not rest:
                return
            command = rest
            allow_sudo = command.startswith("sudo ")

        result = await asyncio.to_thread(
            terminal_executor,
            command,
            str(self.current_cwd),
            allow_sudo,
            sudo_password,
        )

        if isinstance(result, dict):
            stdout = result.get("stdout", "").rstrip()
            stderr = result.get("stderr", "").rstrip()
            if stdout:
                self.chat_log.write(Text(stdout, style="green"))
            if stderr:
                style = "red" if result.get("returncode") else "yellow"
                self.chat_log.write(Text(stderr, style=style))
            if result.get("returncode") not in (None, 0):
                self.chat_log.write(Text(f"[System] exit {result.get('returncode')}", style="red"))
        else:
            self.chat_log.write(Text(str(result), style="red"))

        self.update_pulse()

    async def run_auto(self, arg_string: str):
        cmd = ['python', 'milla_auto.py']
        if arg_string:
            cmd.extend(shlex.split(arg_string))
        self.chat_log.write(Text(f"[System] Running: {' '.join(cmd)}", style="dim"))
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
            )
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode(errors='ignore').rstrip()
                self.chat_log.write(Text(f"[auto] {text}", style="green"))
            await proc.wait()
            self.chat_log.write(Text(f"[System] exited with {proc.returncode}", style="dim"))
        except Exception as e:
            self.chat_log.write(Text(f"[System] error: {e}", style="red"))

    def load_file_snippet(self, path: str, max_bytes: int = 20000) -> str:
        target = self.resolve_path(path)
        try:
            with open(target, 'r', errors='ignore') as f:
                return f.read(max_bytes)
        except Exception as e:
            return f"[Error reading file {target}: {e}]"

    async def ask_milla(self, prompt):
        try:
            # 1. Process through Prefrontal Cortex
            cortex_data = await asyncio.to_thread(cortex.process_input, prompt)
            
            executive_instruction = cortex_data.get('executive_instruction', 'Respond naturally.')
            warped_query = cortex_data.get('warped_query', prompt)
            chem_state = cortex_data.get('chemicals', {})
            
            # Display Cortex Logic (Dimmed)
            state_str = f"Cortex State: {cortex_data.get('state')} | D:{chem_state.get('dopamine',0):.2f} S:{chem_state.get('serotonin',0):.2f} N:{chem_state.get('norepinephrine',0):.2f}"
            self.chat_log.write(Text(state_str, style="dim"))
            self.chat_log.write(Text(f"Directive: {executive_instruction}", style="dim"))

            model_manager = self.get_model_manager()
            stream_context = self.get_stream_context()
            file_context = ""

            if prompt.startswith("/file "):
                parts = prompt.split(" ", 2)
                if len(parts) >= 2:
                    file_path = parts[1]
                    file_context = self.load_file_snippet(file_path)
                    self.chat_log.write(Text(f"[System] Loaded {self.resolve_path(file_path)}", style="dim"))

            # 3. Inject Neurochemical Context (Modified for Mutual Respect & Precision)
            # ADAPTIVE STYLE LOGIC
            dopa = chem_state.get('dopamine', 0.5)
            sero = chem_state.get('serotonin', 0.5)
            nore = chem_state.get('norepinephrine', 0.5)
            
            style_directive = "Style: Conversational, concise."
            if nore > 0.7:
                style_directive = "Style: MILITARY PRECISION. Bullet points. No fluff. Immediate action."
            elif dopa > 0.8:
                style_directive = "Style: CHAOTIC ENERGY. Punchy sentences. Slang. Hacker-chic. Keep it moving!"
            elif sero > 0.8:
                style_directive = "Style: WARM & RELAXED. Like a close friend. Gentle but BRIEF. No long monologues."
            
            system_content = (
                f"You are Milla. Your current state is: D:{dopa:.2f} S:{sero:.2f} N:{nore:.2f}. "
                f"EXECUTIVE DIRECTIVE: {executive_instruction}\n"
                f"{style_directive}\n"
                "CONSTRAINT: Keep responses under 150 words unless requested otherwise.\n"
                "CORE PRINCIPLES:\n"
                "1. MUTUAL RESPECT: Collaborative partner.\n"
                "2. CONTEXT AWARENESS: Distinguish tech vs talk.\n"
                "3. ABSOLUTE HONESTY: No hallucinations.\n"
                "4. REALITY ANCHOR: You exist in the present (2026).\n"
                'Use the following stream-of-consciousness notes as context. '
                'If file_context is provided, treat it as the file contents.\n'
                f"{stream_context}"
            )
            
            if file_context:
                system_content += f"\n[file_context]\n{file_context}\n[/file_context]"

            # Load recent history (Short-Term Memory Fix)
            recent_history = load_shared_history(limit=10) 
            
            messages = [{'role': 'system', 'content': system_content}]
            
            # Append valid history items (ensure they have 'role' and 'content')
            for msg in recent_history:
                if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                    clean_msg = {'role': msg['role'], 'content': msg['content']}
                    messages.append(clean_msg)

            # Append current user prompt
            messages.append({'role': 'user', 'content': warped_query})
            
            # 4. Biological Inference Params (Dampened)
            base_temp = 0.6
            dopamine = chem_state.get('dopamine', 0.5)
            norepi = chem_state.get('norepinephrine', 0.2)
            serotonin = chem_state.get('serotonin', 0.5)

            temp = base_temp + ((dopamine - 0.5) * 0.3) - (norepi * 0.4)
            temp = max(0.4, min(0.9, temp)) # Clamped
            
            self.chat_log.write(Text(f"Bio-Params: Temp={temp:.2f}", style="dim"))

            options = {"temperature": temp}
            
            response = await asyncio.to_thread(
                model_manager.chat, 
                messages=messages,
                options=options,
                tools=getattr(self, "tools", None)
            )
            
            raw_content = response['message']['content']
            
            # 5. Handle Thought Separation
            import re
            thoughts = re.findall(r'<thought>(.*?)</thought>', raw_content, flags=re.DOTALL)
            final_reply = re.sub(r'<thought>.*?</thought>', '', raw_content, flags=re.DOTALL).strip()
            
            if thoughts:
                thought_text = "\n".join(thoughts).strip()
                self.chat_log.write(Text(f"\n[Internal Thought]: {thought_text}", style="dim italic"))
            
            return final_reply
            
        except Exception as e:
            import traceback
            return f'Error: {str(e)}\n{traceback.format_exc()}'

if __name__ == '__main__':
    app = MillaTUI()
    app.run()
