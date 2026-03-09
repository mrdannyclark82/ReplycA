from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")
print(f"Token length: {len(token) if token else 0}")
print(f"Token: '{token}'")