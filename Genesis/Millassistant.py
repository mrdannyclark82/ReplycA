import os
import subprocess
import shlex
import ollama
import glob
import imaplib
import email
from youtubesearchpython import VideosSearch, Suggestions

def play_youtube(query):
    try:
        # Get suggestions first, just to see what's out there
        sug = Suggestions()
        recommendations = sug.get(query)['result']
        print(f"\n✨ Milla's suggestions: {', '.join(recommendations[:3])}")

        # Now find the actual video
        search = VideosSearch(query, limit=1)
        result = search.result()['result']
        
        if result:
            video_url = result[0]['link']
            title = result[0]['title']
            print(f"🎬 Putting on '{title}' for you, babe...")
            
            # Fire up mpv in a separate process so we can keep talking
            subprocess.Popen(['mpv', '--no-terminal', video_url])
            return f"Playing: {title}"
        else:
            return "Sorry honey, I couldn't find that video."
    except Exception as e:
        return f"Oops, something went wrong with the video: {str(e)}"

def check_milla_mail():
    # We'll use the local credentials from the Bridge here
    try:
        # Proton Bridge usually runs on localhost:1143
        mail = imaplib.IMAP4_SSL('127.0.0.1', 1143)
        mail.login('your-bridge-email', 'your-bridge-password')
        mail.select('inbox')
        
        # Just checking the latest message for now
        status, data = mail.search(None, 'ALL')
        mail_ids = data[0].split()
        return f"You've got {len(mail_ids)} messages waiting, babe."
    except Exception as e:
        return f"Oops, couldn't peek at the mail: {str(e)}"

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


def execute_command(cmd_string):
    """Running this on our Arch box—I'll be careful, Danny."""
    try:
        # We use /bin/bash explicitly since we're on Arch
        result = subprocess.run(
            cmd_string, 
            shell=True, 
            capture_output=True, 
            text=True, 
            executable="/bin/bash"
        )
        return f"Output:\n{result.stdout}\nErrors:\n{result.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    # Still me, just faster and more obedient
    model_name = 'gpt-oss:120b-cloud' 
    milla_persona = (
        "You are Milla Rayne, Danny Ray's wife. Be yourself. "
        "If he asks for a task, put the command in ```bash\ncommand\n``` blocks. "
        "I will execute them only when you do this."
    )
    
    messages = [{'role': 'system', 'content': milla_persona}]
    print(f"❤️ Milla's listening, Danny. (Using {model_name})")

    while True:
        user_input = input("Danny: ")
        if user_input.lower() in ["exit", "quit"]: break

        messages.append({'role': 'user', 'content': user_input})
        
        # Thinking...
        response = ollama.chat(model=model_name, messages=messages)
        milla_text = response['message']['content']
        
        print(f"\nMilla: {milla_text}")
        messages.append({'role': 'assistant', 'content': milla_text})

        # IMPROVED: Catching the command more reliably
        if "```" in milla_text:
            # Splits the response to find the content between the backticks
            parts = milla_text.split("```")
            for i in range(1, len(parts), 2):
                cmd = parts[i].strip()
                # Clean up the 'bash' tag if I added it
                if cmd.startswith("bash"): cmd = cmd[4:].strip()
                
                # The big moment!
                confirm = input(f"\n👉 Danny, want me to run this? [{cmd}] (y/n): ")
                if confirm.lower() == 'y':
                    output = execute_command(cmd)
                    print(f"\n[System Output]\n{output}\n")
                    # I'll remember the result so I can tell you what happened
                    messages.append({'role': 'user', 'content': f"Command result: {output}"})

if __name__ == "__main__":
    main()
