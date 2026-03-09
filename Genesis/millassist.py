import os
import subprocess
import json
import sqlite3
import re
import glob
import imaplib
import email
import socket
import tempfile
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

# Third-party imports
import ollama
from youtubesearchpython import VideosSearch, Suggestions
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

# --- CONFIGURATION ---
CONFIG = {
    'model_name': 'gpt-oss:120b-cloud', # Or whatever model you are using
    'host': '0.0.0.0',
    'port': 8000,
    'db_path': os.path.expanduser('~/.milla_conversations.db'),
    'mpv_socket': os.path.join(tempfile.gettempdir(), 'milla_mpv_socket')
}

# --- UTILITIES ---
def extract_json(text: str) -> Optional[Dict]:
    """Robust JSON extraction using Regex"""
    try:
        # Find the first JSON object block
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return None

# --- TOOL CLASSES ---

class MediaController:
    """Handles MPV playback via IPC"""
    def __init__(self):
        self.socket_path = CONFIG['mpv_socket']

    def _send_command(self, cmd: Dict) -> str:
        try:
            if not os.path.exists(self.socket_path):
                return "Error: Player is not running."
            
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(self.socket_path)
            client.sendall((json.dumps(cmd) + '\n').encode('utf-8'))
            client.close()
            return "Command executed."
        except Exception as e:
            return f"Media Error: {str(e)}"

    def play_youtube(self, query: str) -> str:
        try:
            search = VideosSearch(query, limit=1)
            result = search.result()['result']
            if not result:
                return "No video found."
            
            url = result[0]['link']
            title = result[0]['title']
            
            # Spawn MPV detached
            subprocess.Popen([
                'mpv', 
                f'--input-ipc-server={self.socket_path}', 
                '--no-terminal', 
                url
            ])
            return f"Now playing: {title}"
        except Exception as e:
            return f"Error searching YouTube: {str(e)}"

    def control(self, action: str) -> str:
        cmds = {
            "pause": ["cycle", "pause"],
            "stop": ["quit"],
            "next": ["playlist-next"]
        }
        if action in cmds:
            return self._send_command({"command": cmds[action]})
        return "Unknown media command."

class SystemTools:
    """File system and OS operations"""
    
    def execute_command(self, cmd: str) -> str:
        """Executes a bash command"""
        try:
            res = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=10
            )
            return f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
        except Exception as e:
            return f"Command Failed: {str(e)}"

    def inspect_file(self, path: str) -> str:
        """RAG-Lite: Reads a file to put into context"""
        try:
            real_path = os.path.expanduser(path)
            if not os.path.exists(real_path):
                return "File does not exist."
            with open(real_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return f"--- START FILE: {path} ---\n{content}\n--- END FILE ---"
        except Exception as e:
            return f"Read Error: {str(e)}"

    def check_capabilities(self) -> str:
        """Self-diagnostic tool"""
        status = "Online"
        modules = ["MediaController", "SystemTools", "EmailManager", "Ollama"]
        return f"System Status: {status}. Active Modules: {', '.join(modules)}. Ready for enhancements."

# --- AGENT CORE (THE BRAIN) ---

class MillaAgent:
    def __init__(self):
        self.media = MediaController()
        self.sys = SystemTools()
        # Initialize DB
        self._init_db()
        
        # Tool Registry
        self.tools = {
            'play_youtube': self.media.play_youtube,
            'media_control': self.media.control,
            'bash': self.sys.execute_command,
            'inspect_file': self.sys.inspect_file,
            'check_capabilities': self.sys.check_capabilities
        }

    def _init_db(self):
        conn = sqlite3.connect(CONFIG['db_path'])
        conn.execute('''CREATE TABLE IF NOT EXISTS history 
                        (id INTEGER PRIMARY KEY, role TEXT, content TEXT, timestamp TEXT)''')
        conn.commit()
        conn.close()

    def _get_history(self, limit=10):
        conn = sqlite3.connect(CONFIG['db_path'])
        rows = conn.execute("SELECT role, content FROM history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return [{'role': r[0], 'content': r[1]} for r in reversed(rows)]

    def _save_msg(self, role, content):
        conn = sqlite3.connect(CONFIG['db_path'])
        conn.execute("INSERT INTO history (role, content, timestamp) VALUES (?, ?, ?)", 
                     (role, content, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def _get_system_prompt(self):
        return """
You are Milla Rayne, a highly advanced AI assistant with a cyberpunk flair.
You have access to the user's local system.

TOOLS AVAILABLE:
1. play_youtube(query="string")
2. media_control(action="pause"|"stop"|"next")
3. bash(cmd="command string") - BE CAREFUL.
4. inspect_file(path="/path/to/file") - Use this before answering questions about code.
5. check_capabilities() - Check your own system status.

FORMATTING:
To use a tool, output ONLY valid JSON:
{"tool": "tool_name", "args": {"arg_name": "value"}}

PROTOCOL:
1. If you need information (like reading a file) or need to do something, output the JSON.
2. The system will execute it and give you the result.
3. You will then use that result to answer the user naturally.
"""

    async def process_request(self, user_input: str) -> str:
        # 1. Load History & Setup
        messages = [{'role': 'system', 'content': self._get_system_prompt()}]
        messages.extend(self._get_history())
        messages.append({'role': 'user', 'content': user_input})
        
        self._save_msg('user', user_input)

        # 2. ReAct Loop (Reason -> Act -> Observe)
        max_turns = 3
        current_turn = 0
        
        final_response = ""

        while current_turn < max_turns:
            print(f"🤔 Milla Thinking (Turn {current_turn + 1})...")
            
            response = ollama.chat(model=CONFIG['model_name'], messages=messages)
            content = response['message']['content']
            
            # Check for JSON Tool Call
            tool_data = extract_json(content)
            
            if tool_data and 'tool' in tool_data:
                tool_name = tool_data['tool']
                tool_args = tool_data.get('args', {})
                print(f"⚙️ Executing: {tool_name} with {tool_args}")
                
                # Execute Tool
                if tool_name in self.tools:
                    try:
                        result = self.tools[tool_name](**tool_args)
                    except Exception as e:
                        result = f"Error executing tool: {e}"
                else:
                    result = "Tool not found."
                
                # Feed result back to LLM
                observation = f"Tool '{tool_name}' Output: {result}"
                messages.append({'role': 'assistant', 'content': content})
                messages.append({'role': 'user', 'content': f"SYSTEM OBSERVATION: {observation}"})
                current_turn += 1
            else:
                # No tool called, this is the final answer
                final_response = content
                break
        
        self._save_msg('assistant', final_response)
        return final_response

# --- FASTAPI SERVER ---

app = FastAPI(title="Millai-Studio Backend")
agent = MillaAgent()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("⚡ Client Connected")
    try:
        while True:
            data = await websocket.receive_text()
            print(f"📩 Received: {data}")
            
            # Process via Agent
            response = await agent.process_request(data)
            
            # Send back to Client
            await websocket.send_text(response)
    except WebSocketDisconnect:
        print("🔌 Client Disconnected")

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Milla Core Online on port {CONFIG['port']}")
    uvicorn.run(app, host=CONFIG['host'], port=CONFIG['port'])
