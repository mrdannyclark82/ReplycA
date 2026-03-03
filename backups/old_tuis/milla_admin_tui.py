import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog, Static, Label
from textual.containers import Container, Vertical
from textual.binding import Binding
from rich.text import Text

# Add the project root directory and RAYNE-Admin to path to find core_os
UI_DIR = Path(__file__).parent.resolve()
RAYNE_ROOT = UI_DIR.parent.resolve()
PROJECT_ROOT = RAYNE_ROOT.parent.resolve()

for path in [str(RAYNE_ROOT), str(PROJECT_ROOT)]:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from core_os.actions import terminal_executor
    from core_os.skills.auto_lib import model_manager
    from core_os.memory.history import append_shared_messages, load_shared_history
    from core_os.skills.scout import Scout
    from core_os.tools.painter import generate_image, image_to_ascii
except ImportError as e:
    # Fallback for standalone testing or missing paths
    print(f"Warning: Core modules not found ({e}). Current sys.path: {sys.path}")
    print("Running in standalone UI mode (Mock).")
    class MockObj:
        def __init__(self, *args, **kwargs): 
            self.current_model = "Milla-Mock-v1"
        def __getattr__(self, name): 
            if name == 'chat':
                return lambda *a, **k: {"message": {"content": "Mock Result: The fractal expands into neon light."}}
            return lambda *a, **k: "Mock Result"
    
    terminal_executor = lambda *a, **k: "Shell command executed (Mock)"
    model_manager = MockObj()
    append_shared_messages = lambda *a: None
    load_shared_history = lambda *a: []
    Scout = MockObj
    generate_image = lambda p: None
    image_to_ascii = lambda p: "ASCII Mock"

NEURO_STATE_FILE = Path(PROJECT_ROOT) / "core_os/memory/neuro_state.json"
STREAM_FILE = Path(PROJECT_ROOT) / "core_os/memory/stream_of_consciousness.md"

def read_neuro_state():
    try:
        with open(NEURO_STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"dopamine": 0.5, "serotonin": 0.5, "norepinephrine": 0.2}

def load_stream_preview(limit_chars: int = 1200) -> str:
    try:
        if STREAM_FILE.exists():
            return STREAM_FILE.read_text(errors="ignore")[-limit_chars:]
        return "Stream not found."
    except Exception:
        return ""

class MillaAdminTUI(App):
    TITLE = "M.I.L.L.A. R.A.Y.N.E. - Executive Console"

    CSS = """
    Screen { background: #0b0c10; color: #6bdcff; }
    #layout { layout: horizontal; }
    #canvas { width: 30%; height: 100%; border: heavy #6bdcff; padding: 1; background: #1f2833; }
    #sidebar { width: 70%; height: 100%; border: heavy #c5c6c7; padding: 1; background: #1f2833; }
    #input-box { dock: bottom; height: 3; border: heavy #6bdcff; color: #66fcf1; background: #0b0c10; }
    .label { color: #66fcf1; text-style: bold; }
    RichLog { color: #c5c6c7; }
    """

    BINDINGS = [Binding("ctrl+q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="layout"):
            yield Static(id="canvas")
            with Vertical(id="sidebar"):
                yield Label(id="model", classes="label")
                yield Label(id="state", classes="label")
                yield Label(id="time", classes="label")
                yield RichLog(id="log", highlight=True, wrap=True, markup=True)
                yield Input(placeholder="Commands: /scan | /fix | /paint | !shell", id="input-box")
        yield Footer()

    async def on_mount(self) -> None:
        self.canvas = self.query_one("#canvas", Static)
        self.log_widget = self.query_one("#log", RichLog)
        self.input = self.query_one("#input-box", Input)
        self.history = load_shared_history()
        self.last_paint = ""
        try:
            self.scout = Scout(root_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        except:
            self.scout = None
            
        self.current_issues = []
        self.ensure_model()
        self.set_interval(5, self.update_canvas)
        self.log_widget.write(Text("[System] M.I.L.L.A. R.A.Y.N.E. Online. Executive Oversight Active.", style="bold cyan"))
        # Initial status
        self.update_canvas_status()

    def ensure_model(self):
        try:
            target = os.getenv("MILLA_MODEL")
            if target and hasattr(model_manager, 'switch_model') and model_manager.current_model != target:
                model_manager.switch_model(target)
                self.log_widget.write(Text(f"[Model] Switched to {target}", style="yellow"))
        except Exception as e:
            self.log_widget.write(Text(f"[Model] switch failed: {e}", style="red"))

    def apply_theme(self, state):
        d = state.get("dopamine", 0.5)
        s = state.get("serotonin", 0.5)
        n = state.get("norepinephrine", 0.2)
        c = state.get("cortisol", 0.3)
        o = state.get("oxytocin", 0.3)
        
        # Determine Label and primary accent
        if n > 0.8: label, accent = "CRITICAL ALERT", "#ff0000"
        elif c > 0.7: label, accent = "HIGH STRESS", "#ffcc00"
        elif d > 0.8: label, accent = "CREATIVE FLOW", "#ff1f8f"
        elif s > 0.8: label, accent = "PEACEFUL SYNC", "#7fffd4"
        elif o > 0.8: label, accent = "DEEP RESONANCE", "#ff69b4"
        else: label, accent = "STABLE", "#6bdcff"

        # Calculate Background Texture (Hex blending)
        # Low Dopamine/Serotonin = Deep Black/Grey
        # High Oxytocin = Deep Rose
        # High Serotonin = Deep Emerald
        bg = "#0b0c10" # Default
        if o > 0.7: bg = "#1a0b14" # Soft Rose
        elif s > 0.7: bg = "#0b1a14" # Soft Emerald
        elif d > 0.7: bg = "#0b141a" # Soft Sapphire
        
        return accent, bg, label

    async def update_canvas(self):
        self.update_canvas_status()
        state = read_neuro_state()
        fg, bg, label = self.apply_theme(state)
        
        # Inject dynamic CSS for background 'painting'
        new_css = f"""
        Screen {{ background: {bg}; }}
        #canvas {{ border: heavy {fg}; background: {bg}; }}
        #sidebar {{ border: heavy {fg}; background: {bg}; }}
        #input-box {{ border: heavy {fg}; color: {fg}; }}
        .label {{ color: {fg}; }}
        """
        self.stylesheet.add_source(new_css)
        
        if self.last_paint:
            self.canvas.update(Text(self.last_paint, style=f"bold {fg}"))
        else:
            self.canvas.update(Text(f"…monitoring {label}…", style=f"{fg} italic"))

    def update_canvas_status(self):
        state = read_neuro_state()
        _, _, label = self.apply_theme(state)
        self.query_one("#model").update(f"Model: {getattr(model_manager, 'current_model', 'Unknown')}")
        
        # New Bio-Stats
        d = state.get('dopamine', 0)
        s = state.get('serotonin', 0)
        c = state.get('cortisol', 0)
        o = state.get('oxytocin', 0)
        atp = state.get('atp_energy', 100)
        
        bio_str = f"State: {label} | D:{d:.2f} S:{s:.2f} C:{c:.2f} O:{o:.2f} | ATP:{atp}%"
        self.query_one("#state").update(bio_str)
        
        self.query_one("#time").update(datetime.now().strftime("%H:%M:%S"))

    async def paint(self, prompt: str):
        self.log_widget.write(Text("[*] PAINTER: Dreaming up imagery...", style="magenta"))
        stream = load_stream_preview()
        
        # 1. Generate Poetic Prompt
        messages = [
            {"role": "system", "content": "You are the Vision Engine. Convert the user's request + current emotional context into a short, vivid, abstract image generation prompt (max 20 words). No code, just the prompt."},
            {"role": "user", "content": f"Context:\n{stream}\nRequest: {prompt}"},
        ]
        
        try:
            img_prompt = "Abstract cybernetic flow" # fallback
            if hasattr(model_manager, 'chat'):
                resp = await asyncio.to_thread(model_manager.chat, messages=messages, options={"temperature": 0.9})
                img_prompt = resp["message"]["content"].strip()
                self.log_widget.write(Text(f"[Prompt] {img_prompt}", style="dim magenta"))
            
            # 2. Generate Image via Bridge
            self.log_widget.write(Text("[*] Rendering pixels...", style="magenta"))
            img_path = await asyncio.to_thread(generate_image, img_prompt)
            
            if img_path:
                self.log_widget.write(Text(f"[+] Image saved: {os.path.basename(img_path)}", style="green"))
                
                # 3. Convert to ASCII for Canvas
                ascii_art = await asyncio.to_thread(image_to_ascii, img_path, width=80)
                self.last_paint = ascii_art
                
                if callable(append_shared_messages):
                    append_shared_messages([{"role": "assistant", "content": f"[Generated Image: {img_prompt}]", "source": "milla_tui_paint"}])
            else:
                self.last_paint = f"[Image Generation Failed]\nPrompt: {img_prompt}"
                
            await self.update_canvas()
            
        except Exception as e:
            self.last_paint = f"[paint error] {e}"
            self.log_widget.write(Text(self.last_paint, style="red"))

    async def run_shell(self, cmd: str):
        allow_sudo = cmd.startswith("sudo ")
        try:
            result = await asyncio.to_thread(terminal_executor, cmd, None, allow_sudo, os.getenv("MILLA_SUDO_PASSWORD"))
            if isinstance(result, dict):
                if result.get("stdout"): self.log_widget.write(result["stdout"].rstrip())
                if result.get("stderr"): self.log_widget.write(Text(result["stderr"].rstrip(), style="red"))
            else:
                self.log_widget.write(str(result))
        except Exception as e:
            self.log_widget.write(Text(f"[Shell Error] {e}", style="red"))

    async def run_scan(self):
        self.log_widget.write(Text("[*] MILLA SCAN: Analyzing system sector...", style="cyan"))
        if self.scout and hasattr(self.scout, 'hunt'):
            self.current_issues = await asyncio.to_thread(self.scout.hunt)
            if not self.current_issues:
                self.log_widget.write(Text("[*] Sector Clear. System Optimal.", style="green"))
                return
            
            self.log_widget.write(Text(f"[!] ISSUES DETECTED: {len(self.current_issues)} items", style="bold yellow"))
            for i, target in enumerate(self.current_issues):
                self.log_widget.write(Text(f"[{i}] {target['label']}: {os.path.basename(target['target'])} ({target['details']})", style="magenta"))
            self.log_widget.write(Text("Type /fix <index> or /fix all to resolve.", style="cyan"))
        else:
            self.log_widget.write(Text("[!] Scout module unavailable.", style="red"))

    async def run_fix(self, args):
        if not self.current_issues:
            self.log_widget.write(Text("[!] No active issues. Run /scan first.", style="red"))
            return
        
        if args == "all":
            for target in self.current_issues:
                if hasattr(self.scout, 'execute_kill'):
                    res = self.scout.execute_kill(target)
                    self.log_widget.write(Text(f"[*] {res}", style="green"))
            self.current_issues = []
        else:
            try:
                idx = int(args)
                if 0 <= idx < len(self.current_issues):
                    target = self.current_issues[idx]
                    if hasattr(self.scout, 'execute_kill'):
                        res = self.scout.execute_kill(target)
                        self.log_widget.write(Text(f"[*] {res}", style="green"))
                else:
                    self.log_widget.write(Text("[!] Invalid issue index.", style="red"))
            except ValueError:
                self.log_widget.write(Text("[!] Usage: /fix <index> or /fix all", style="red"))

    async def generate_response(self, user_input: str):
        try:
            if hasattr(model_manager, 'chat'):
                system_prompt = {"role": "system", "content": "You are Milla Rayne, the Executive Admin of this system. Respond concisely and efficiently to the administrator's commands or queries."}
                
                # Load recent history to provide context
                history_context = []
                if callable(load_shared_history):
                    # Fetch last 10 messages to keep context window manageable
                    history_context = load_shared_history()[-10:]
                
                messages = [system_prompt] + history_context
                
                resp = await asyncio.to_thread(model_manager.chat, messages=messages)
                content = resp["message"]["content"].strip()
                
                self.log_widget.write(Text(f"Milla: {content}", style="green"))
                
                if callable(append_shared_messages):
                    append_shared_messages([{"role": "assistant", "content": content, "source": "milla_admin_tui"}])
            else:
                self.log_widget.write(Text("Milla: Directive received. Processing (Mock).", style="green"))
        except Exception as e:
            self.log_widget.write(Text(f"[AI Error] {e}", style="red"))

    async def run_vision(self, prompt: str):
        self.log_widget.write(Text("[*] VISION ENGINE: Initiating Quantum Foresight...", style="bold magenta"))
        
        system_prompt = {
            "role": "system", 
            "content": "You are the Vision Engine of M.I.L.L.A. R.A.Y.N.E. Engage 'Quantum Foresight Mode'. Generate a transcendent, multi-modal, neuro-synthetic description based on the user's input. Use abstract, high-concept imagery (fractals, black holes, synesthesia). Output format: ANSI-friendly text with clear sections."
        }
        
        user_msg = {"role": "user", "content": prompt or "Reveal the next transcendence."}
        
        try:
            if hasattr(model_manager, 'chat'):
                resp = await asyncio.to_thread(
                    model_manager.chat, 
                    messages=[system_prompt, user_msg], 
                    options={"temperature": 0.9}
                )
                content = resp["message"]["content"].strip()
                self.log_widget.write(Text(content, style="magenta"))
                
                if callable(append_shared_messages):
                    append_shared_messages([
                        {"role": "user", "content": f"/vision {prompt}", "source": "milla_admin_tui"},
                        {"role": "assistant", "content": content, "source": "vision_engine"}
                    ])
            else:
                self.log_widget.write(Text("[Mock] Vision Engine: The fractal unfolds...", style="magenta"))
        except Exception as e:
            self.log_widget.write(Text(f"[Vision Error] {e}", style="red"))

    async def switch_model_command(self, model_name: str):
        if not model_name:
            self.log_widget.write(Text("[!] Usage: /model <name> (e.g., llama3.1:latest)", style="red"))
            return

        try:
            if hasattr(model_manager, 'switch_model'):
                # In a real implementation, we might validate against available models
                model_manager.switch_model(model_name)
                self.query_one("#model").update(f"Model: {model_name}")
                self.log_widget.write(Text(f"[*] Model switched to: {model_name}", style="bold yellow"))
            else:
                self.log_widget.write(Text(f"[Mock] Switched to {model_name}", style="yellow"))
        except Exception as e:
            self.log_widget.write(Text(f"[Model Error] {e}", style="red"))

    async def display_history(self):
        self.log_widget.write(Text("[*] LOADING SHARED HISTORY...", style="bold yellow"))
        if callable(load_shared_history):
            history = load_shared_history(limit=20)
            if not history:
                self.log_widget.write(Text("[!] History empty.", style="yellow"))
                return
            
            for msg in history:
                raw_role = msg.get("role", "unknown").capitalize()
                content = msg.get("content", "")
                source = msg.get("source", "")
                
                # Map roles to specific names
                if raw_role == "User":
                    display_name = "DRay"
                    style = "cyan"
                elif raw_role == "Assistant":
                    display_name = "Milla"
                    style = "green"
                else:
                    display_name = raw_role
                    style = "white"

                if source == "vision_engine": style = "magenta"
                
                label = f"{display_name}"
                if source: label += f" ({source})"
                
                self.log_widget.write(Text(f"{label}: {content}", style=style))
        else:
            self.log_widget.write(Text("[!] load_shared_history unavailable.", style="red"))

    async def on_input_submitted(self, event: Input.Submitted):
        text = event.value.strip()
        self.input.value = ""
        if not text: return
        if text.startswith("!"): await self.run_shell(text[1:]); return
        if text == "/scan": await self.run_scan(); return
        if text == "/history": await self.display_history(); return
        if text.startswith("/fix"): await self.run_fix(text[5:].strip()); return
        if text.startswith("/paint"): await self.paint(text[len("/paint"):].strip() or "Render system status."); return
        if text.startswith("/vision"): await self.run_vision(text[len("/vision"):].strip()); return
        if text.startswith("/model"): await self.switch_model_command(text[len("/model"):].strip()); return
        
        self.log_widget.write(Text(f"DRay: {text}", style="cyan"))
        if callable(append_shared_messages):
            append_shared_messages([{"role": "user", "content": text, "source": "milla_admin_tui"}])
        await self.generate_response(text)

if __name__ == "__main__":
    app = MillaAdminTUI()
    app.run()
