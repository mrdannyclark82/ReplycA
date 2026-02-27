import os
import time
import requests
import textwrap
from PIL import Image
from io import BytesIO

CACHE_DIR = "core_os/media"
LATEST_IMG = "latest_paint.jpg"

def generate_image(prompt):
    """
    Generates a high-quality image from a text prompt using Hugging Face Inference API.
    Uses HF_TOKEN from .env.
    """
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        
    # Load token
    token = None
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("HF_TOKEN="):
                    token = line.split("=")[1].strip()
                    break
    
    if not token:
        print("Painter Error: HF_TOKEN not found in .env")
        return None

    # SDXL Endpoint (Updated Router)
    API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        payload = {"inputs": prompt}
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            img_data = response.content
            path = os.path.join(CACHE_DIR, f"paint_{int(time.time())}.png")
            latest_path = os.path.join(CACHE_DIR, LATEST_IMG)
            
            with open(path, "wb") as f:
                f.write(img_data)
            with open(latest_path, "wb") as f:
                f.write(img_data)
                
            return latest_path
        else:
            print(f"Painter API Error ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"Painter Exception: {e}")
    
    return None

def image_to_ascii(image_path, width=60):
    """
    Converts an image to an ASCII representation.
    """
    try:
        img = Image.open(image_path)
        
        # Resize
        aspect_ratio = img.height / img.width
        new_height = int(aspect_ratio * width * 0.55)
        img = img.resize((width, new_height))
        img = img.convert('L') # Grayscale
        
        pixels = img.getdata()
        chars = ["@", "J", "D", "%", "*", "P", "+", "Y", "$", ",", "."]
        
        new_pixels = [chars[pixel // 25] for pixel in pixels]
        new_pixels = ''.join(new_pixels)
        
        ascii_image = [new_pixels[index:index + width] for index in range(0, len(new_pixels), width)]
        return "\n".join(ascii_image)
        
    except Exception as e:
        return f"[ASCII Render Failed: {e}]"

if __name__ == "__main__":
    # Test
    p = generate_image("cyberpunk terminal hugging a void")
    if p:
        print(image_to_ascii(p))
