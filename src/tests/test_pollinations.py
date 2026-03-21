import requests
from urllib.parse import quote

def generate_image(prompt):
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=800&height=600&nologo=true"
    response = requests.get(url)
    if response.status_code == 200:
        with open("pollination_test.jpg", "wb") as f:
            f.write(response.content)
        print("Image saved to pollination_test.jpg")
        return True
    return False

generate_image("a beautiful highly detailed cyberpunk neon terminal interface glowing in the dark")
