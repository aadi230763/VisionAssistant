import requests
import os
from dotenv import load_dotenv

load_dotenv()

def speak(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{os.getenv('ELEVENLABS_VOICE_ID')}"

    headers = {
        "xi-api-key": os.getenv("ELEVENLABS_API_KEY"),
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.8
        }
    }

    response = requests.post(url, json=payload, headers=headers)

    with open("alert.mp3", "wb") as f:
        f.write(response.content)

    os.system("start alert.mp3")  # Windows
