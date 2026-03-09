import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()
VENICE_API_KEY = os.getenv("VENICE_API_KEY")

def generate_image(prompt):
    url = "https://api.venice.ai/api/v1/image/generate"
    headers = {
        "Authorization": f"Bearer {VENICE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "fluently-xl",
        "prompt": prompt,
        "width": 1024,
        "height": 1024
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        if "images" in data and len(data["images"]) > 0:
            image_b64 = data["images"][0]
            with open("venice_test.png", "wb") as f:
                f.write(base64.b64decode(image_b64))
            print("Image saved to venice_test.png")
            return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    generate_image("A futuristic cyberpunk terminal glowing in a dark room")
