import requests
import os
import sys
import shlex
import subprocess
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

    audio_path = "alert.mp3"
    with open(audio_path, "wb") as f:
        f.write(response.content)

    # Playback only (keep ElevenLabs request/response logic unchanged)
    if sys.platform == "darwin":
        try:
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 1024:
                with open(audio_path, "rb") as f:
                    head = f.read(16)
                # If ElevenLabs returns an error body (often JSON), don't feed it to afplay.
                if head.startswith(b"{") or head.startswith(b"<"):
                    return
                subprocess.run(["afplay", audio_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            return
    else:
        os.system(f"start {audio_path}")  # Windows
