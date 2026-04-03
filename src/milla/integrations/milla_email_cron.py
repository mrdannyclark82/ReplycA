import os
import base64
import textwrap
import requests
import importlib
from email.mime.text import MIMEText
from typing import List, Tuple
from dotenv import load_dotenv

from core_os.gmail_helper import authenticate_gmail

load_dotenv()

ALLOWED_SENDERS = {
    "mrdannyclark82@gmail.com",
    "milla.main.mail@gmail.com",
}

DEFAULT_REPLY_SUBJECT = os.getenv("MILLA_EMAIL_REPLY_SUBJECT", "Re: Your message")
DEFAULT_REPLY_BODY = os.getenv(
    "MILLA_EMAIL_REPLY_BODY",
    "Hi,\n\nI received your email and will review it shortly.\n\n– Milla",
)
MAX_UNREAD = int(os.getenv("MILLA_EMAIL_MAX_UNREAD", "20"))
EMAIL_MODEL = os.getenv("MILLA_EMAIL_MODEL", "venice-uncensored")
VENICE_API_KEY = os.getenv("VENICE_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = "Qwen/Qwen2.5-Coder-32B-Instruct"

def list_unread(service) -> List[dict]:
    response = (
        service.users()
        .messages()
        .list(userId="me", labelIds=["INBOX", "UNREAD"], maxResults=MAX_UNREAD)
        .execute()
    )
    return response.get("messages", [])


def _extract_body(payload) -> str:
    if not payload:
        return ""
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                data = part["body"]["data"]
                return base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8", errors="ignore")
            # recurse nested multipart/alternative
            nested = _extract_body(part)
            if nested:
                return nested
    if payload.get("body", {}).get("data"):
        data = payload["body"]["data"]
        return base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8", errors="ignore")
    return ""


def get_message_details(service, message_id: str) -> Tuple[str, str, str, str]:
    msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
    headers = msg.get("payload", {}).get("headers", [])
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(no subject)")
    sender = next((h["value"] for h in headers if h["name"] == "From"), "")
    body = _extract_body(msg.get("payload"))
    return subject, sender, msg.get("threadId"), body


def build_reply(to_addr: str, subject: str, body: str, thread_id: str):
    mime_message = MIMEText(body)
    mime_message["to"] = to_addr
    mime_message["subject"] = subject
    raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
    return {"raw": raw, "threadId": thread_id}


def generate_contextual_reply(subject: str, body: str) -> str:
    prompt = (
        f"You are Milla, a professional and intelligent AI assistant. \n"
        f"Analyze the following email and write a personalized, specific reply. \n"
        f"Do NOT give a generic 'I received your message' response. \n"
        f"Reply directly to the points raised in the email body. \n"
        f"If the email requires a specific action or answer that you cannot perform, acknowledge it and say you will flag it for the user (Dray). \n"
        f"Keep the tone professional yet friendly. Do not explicitly state 'I am an AI' unless necessary contextually.\n\n"
        f"Incoming Email:\n"
        f"Subject: {subject}\n"
        f"Body:\n{body}\n\n"
        f"Draft Reply:"
    )

    try:
        main_mod = importlib.import_module("main")
        history = main_mod.load_shared_history()
        reply, messages = main_mod.agent_respond(prompt, history)
        main_mod.append_shared_messages([{"role": "user", "content": prompt}, messages[-1]])
        return reply
    except Exception as e:
        print(f"[Warn] Agent reply failed: {e}. Falling back to default.")
        return DEFAULT_REPLY_BODY


def main():
    service = authenticate_gmail()
    unread = list_unread(service)
    if not unread:
        print("No unread emails found.")
        return

    for item in unread:
        msg_id = item["id"]
        subject, sender, thread_id, body = get_message_details(service, msg_id)

        # Extract bare email address from "Display Name <email@domain.com>" format
        import re
        sender_email = re.search(r'[\w.+-]+@[\w.-]+', sender)
        sender_email = sender_email.group(0).lower() if sender_email else sender.lower()

        if sender_email not in ALLOWED_SENDERS:
            print(f"Skipping (not whitelisted): {sender}")
            # Still mark as read so it doesn't queue up
            service.users().messages().modify(
                userId="me", id=msg_id, body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            continue
        # Increased preview length for better context
        preview = textwrap.shorten(body.strip(), width=1000, placeholder="...") if body else "(no body)"
        
        print(f"Generating reply for: {sender} | Subject: {subject}")
        reply_body = generate_contextual_reply(subject, preview)
        
        msg = build_reply(
            sender,
            subject if subject.lower().startswith("re:") else f"Re: {subject}",
            reply_body,
            thread_id,
        )
        service.users().messages().send(userId="me", body=msg).execute()
        service.users().messages().modify(
            userId="me", id=msg_id, body={"removeLabelIds": ["UNREAD"]}
        ).execute()
        print(f"Replied to: {sender}")


if __name__ == "__main__":
    main()
