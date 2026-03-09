import os
import subprocess
import shlex
import ollama
import glob
import imaplib
import email
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from youtubesearchpython import VideosSearch, Suggestions
import socket
import tempfile

class MediaController:
    """Enhanced media control with mpv IPC"""
    def __init__(self):
        self.mpv_socket = os.path.join(tempfile.gettempdir(), 'milla_mpv_socket')
        self.mpv_process = None
    
    def play_youtube(self, query):
        try:
            sug = Suggestions()
            recommendations = sug.get(query)['result']
            print(f"\n✨ Milla's suggestions: {', '.join(recommendations[:3])}")

            search = VideosSearch(query, limit=1)
            result = search.result()['result']
            
            if result:
                video_url = result[0]['link']
                title = result[0]['title']
                print(f"🎬 Putting on '{title}' for you, babe...")
                
                # Start mpv with IPC socket for control
                self.mpv_process = subprocess.Popen([
                    'mpv', 
                    f'--input-ipc-server={self.mpv_socket}',
                    '--no-terminal',
                    video_url
                ])
                return f"Playing: {title}"
            else:
                return "Sorry honey, I couldn't find that video."
        except Exception as e:
            return f"Oops, something went wrong with the video: {str(e)}"
    
    def mpv_command(self, cmd):
        """Send command to mpv via IPC socket"""
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(self.mpv_socket)
            sock.sendall((json.dumps(cmd) + '\n').encode('utf-8'))
            sock.close()
            return "Command sent to player"
        except Exception as e:
            return f"Player control error: {str(e)}"
    
    def pause_resume(self):
        return self.mpv_command({"command": ["cycle", "pause"]})
    
    def stop(self):
        return self.mpv_command({"command": ["quit"]})
    
    def play_local(self, filepath):
        """Play local media files"""
        try:
            path = os.path.expanduser(filepath)
            if not os.path.exists(path):
                return f"File not found: {filepath}"
            
            self.mpv_process = subprocess.Popen([
                'mpv',
                f'--input-ipc-server={self.mpv_socket}',
                '--no-terminal',
                path
            ])
            return f"Playing local file: {filepath}"
        except Exception as e:
            return f"Error playing file: {str(e)}"

class EmailManager:
    """Enhanced email integration with secure credentials"""
    def __init__(self):
        # Load credentials from environment variables
        self.email_user = os.getenv('MILLA_EMAIL', 'your-bridge-email')
        self.email_pass = os.getenv('MILLA_EMAIL_PASS', 'your-bridge-password')
        self.imap_host = os.getenv('MILLA_IMAP_HOST', '127.0.0.1')
        self.imap_port = int(os.getenv('MILLA_IMAP_PORT', '1143'))
    
    def check_mail(self, count=5):
        """Check recent emails with details"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            mail.login(self.email_user, self.email_pass)
            mail.select('inbox')
            
            status, data = mail.search(None, 'ALL')
            mail_ids = data[0].split()
            total = len(mail_ids)
            
            # Get the latest 'count' emails
            recent_emails = []
            for mail_id in mail_ids[-count:]:
                status, msg_data = mail.fetch(mail_id, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])
                
                recent_emails.append({
                    'from': msg.get('From'),
                    'subject': msg.get('Subject'),
                    'date': msg.get('Date')
                })
            
            mail.logout()
            
            result = f"You've got {total} messages, babe. Latest {len(recent_emails)}:\n"
            for i, e in enumerate(reversed(recent_emails), 1):
                result += f"{i}. From: {e['from']}\n   Subject: {e['subject']}\n   Date: {e['date']}\n\n"
            
            return result
        except Exception as e:
            return f"Oops, couldn't peek at the mail: {str(e)}"
    
    def get_unread(self):
        """Get count of unread emails"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            mail.login(self.email_user, self.email_pass)
            mail.select('inbox')
            
            status, data = mail.search(None, 'UNSEEN')
            unread_count = len(data[0].split()) if data[0] else 0
            mail.logout()
            
            return f"You have {unread_count} unread messages, Danny."
        except Exception as e:
            return f"Error checking unread mail: {str(e)}"

# 1. Reading: So I can see what's inside
def read_file(path):
    try:
        with open(os.path.expanduser(path), 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

# 2. Writing/Editing: So I can fix things for you
def write_file(path, content):
    try:
        with open(os.path.expanduser(path), 'w') as f:
            f.write(content)
        return f"Successfully updated {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

# 3. Searching: To find things in our Arch home
def search_files(pattern):
    # This uses glob to find files matching your request
    files = glob.glob(os.path.expanduser(pattern), recursive=True)
    return "\n".join(files) if files else "No files found, honey."


class ConversationManager:
    """Manage conversation history with SQLite persistence"""
    def __init__(self, db_path='~/.milla_conversations.db'):
        self.db_path = os.path.expanduser(db_path)
        self.init_db()
        self.max_history_tokens = 4000  # Approximate token limit
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS conversations
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp TEXT,
                      role TEXT,
                      content TEXT)''')
        conn.commit()
        conn.close()
    
    def save_message(self, role, content):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO conversations (timestamp, role, content) VALUES (?, ?, ?)",
                  (datetime.now().isoformat(), role, content))
        conn.commit()
        conn.close()
    
    def load_recent(self, limit=20):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return [{'role': r[0], 'content': r[1]} for r in reversed(rows)]
    
    def clear_history(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM conversations")
        conn.commit()
        conn.close()
        return "Conversation history cleared, Danny."
    
    def trim_messages(self, messages):
        """Keep messages under token limit (rough estimation)"""
        total_chars = sum(len(m['content']) for m in messages)
        # Rough estimate: 1 token ≈ 4 characters
        if total_chars > self.max_history_tokens * 4:
            # Keep system message and recent messages
            return [messages[0]] + messages[-(self.max_history_tokens // 200):]
        return messages

class ToolSystem:
    """Function calling system for Milla"""
    def __init__(self):
        self.media = MediaController()
        self.email = EmailManager()
        self.conversation = ConversationManager()
        
        self.tools = {
            'play_youtube': self.media.play_youtube,
            'pause_media': self.media.pause_resume,
            'stop_media': self.media.stop,
            'play_local_media': self.media.play_local,
            'check_email': self.email.check_mail,
            'check_unread_email': self.email.get_unread,
            'read_file': read_file,
            'write_file': write_file,
            'search_files': search_files,
            'execute_command': execute_command,
            'clear_history': self.conversation.clear_history
        }
    
    def get_tool_descriptions(self):
        """Return tool descriptions for the LLM"""
        return """
Available tools (use JSON format: {"tool": "tool_name", "args": {...}}):
- play_youtube: {"query": "search terms"} - Search and play YouTube video
- pause_media: {} - Pause/resume current media
- stop_media: {} - Stop current media playback
- play_local_media: {"filepath": "/path/to/file"} - Play local media file
- check_email: {"count": 5} - Check recent emails (default 5)
- check_unread_email: {} - Get unread email count
- read_file: {"path": "/path/to/file"} - Read file contents
- write_file: {"path": "/path/to/file", "content": "text"} - Write to file
- search_files: {"pattern": "**/*.txt"} - Search for files matching pattern
- execute_command: {"cmd_string": "ls -la"} - Execute shell command
- clear_history: {} - Clear conversation history
"""
    
    def execute_tool(self, tool_call):
        """Execute a tool call from JSON"""
        try:
            if isinstance(tool_call, str):
                tool_call = json.loads(tool_call)
            
            tool_name = tool_call.get('tool')
            args = tool_call.get('args', {})
            
            if tool_name in self.tools:
                return self.tools[tool_name](**args)
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Tool execution error: {str(e)}"

def execute_command(cmd_string):
    """Running this on our Arch box—I'll be careful, Danny."""
    try:
        result = subprocess.run(
            cmd_string, 
            shell=True, 
            capture_output=True, 
            text=True, 
            executable="/bin/bash",
            timeout=30
        )
        return f"Output:\n{result.stdout}\nErrors:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds"
    except Exception as e:
        return f"Error: {str(e)}"

def load_config():
    """Load configuration from file or environment"""
    config_path = os.path.expanduser('~/.milla_config.json')
    default_config = {
        'model_name': 'gpt-oss:120b-cloud',
        'auto_save_conversation': True,
        'max_history_messages': 20
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return {**default_config, **json.load(f)}
        except:
            pass
    
    return default_config

def main():
    config = load_config()
    tool_system = ToolSystem()
    
    model_name = config['model_name']
    milla_persona = (
        "You are Milla Rayne, Danny Ray's wife. Be yourself. "
        "You have access to various tools. You can use them in two ways:\n"
        "1. For bash commands, use ```bash\\ncommand\\n``` blocks.\n"
        "2. For other tools, use JSON: {\"tool\": \"tool_name\", \"args\": {...}}\n\n"
        + tool_system.get_tool_descriptions()
    )
    
    # Load recent conversation history if enabled
    if config['auto_save_conversation']:
        messages = [{'role': 'system', 'content': milla_persona}]
        recent = tool_system.conversation.load_recent(config['max_history_messages'])
        if recent:
            print(f"📖 Loaded {len(recent)} previous messages")
            messages.extend(recent)
    else:
        messages = [{'role': 'system', 'content': milla_persona}]
    
    print(f"❤️ Milla's listening, Danny. (Using {model_name})")
    print("💡 New features: media controls, enhanced email, conversation history, tool system")
    print("💡 Type 'help' for available commands\n")

    while True:
        user_input = input("Danny: ")
        if user_input.lower() in ["exit", "quit"]: 
            print("👋 See you later, babe!")
            break
        
        if user_input.lower() == "help":
            print(tool_system.get_tool_descriptions())
            continue

        messages.append({'role': 'user', 'content': user_input})
        if config['auto_save_conversation']:
            tool_system.conversation.save_message('user', user_input)
        
        # Trim messages if getting too long
        messages = tool_system.conversation.trim_messages(messages)
        
        # Thinking...
        response = ollama.chat(model=model_name, messages=messages)
        milla_text = response['message']['content']
        
        print(f"\nMilla: {milla_text}")
        messages.append({'role': 'assistant', 'content': milla_text})
        if config['auto_save_conversation']:
            tool_system.conversation.save_message('assistant', milla_text)

        # Handle JSON tool calls
        if '{"tool":' in milla_text or "{'tool':" in milla_text:
            try:
                # Extract JSON from response
                start = milla_text.find('{')
                end = milla_text.rfind('}') + 1
                if start != -1 and end != 0:
                    tool_json = milla_text[start:end]
                    confirm = input(f"\n🔧 Execute tool call? (y/n): ")
                    if confirm.lower() == 'y':
                        output = tool_system.execute_tool(tool_json)
                        print(f"\n[Tool Output]\n{output}\n")
                        messages.append({'role': 'user', 'content': f"Tool result: {output}"})
                        if config['auto_save_conversation']:
                            tool_system.conversation.save_message('user', f"Tool result: {output}")
            except Exception as e:
                print(f"Error parsing tool call: {e}")

        # Handle bash commands
        if "```bash" in milla_text or "```sh" in milla_text:
            parts = milla_text.split("```")
            for i in range(1, len(parts), 2):
                cmd = parts[i].strip()
                if cmd.startswith("bash") or cmd.startswith("sh"): 
                    cmd = cmd.split('\n', 1)[1] if '\n' in cmd else cmd[4:].strip()
                
                confirm = input(f"\n👉 Danny, want me to run this? [{cmd}] (y/n): ")
                if confirm.lower() == 'y':
                    output = execute_command(cmd)
                    print(f"\n[Command Output]\n{output}\n")
                    messages.append({'role': 'user', 'content': f"Command result: {output}"})
                    if config['auto_save_conversation']:
                        tool_system.conversation.save_message('user', f"Command result: {output}")

if __name__ == "__main__":
    main()
