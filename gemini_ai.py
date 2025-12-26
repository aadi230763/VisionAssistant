from google import genai
from PIL import Image
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "models/gemini-2.0-flash"

def analyze_scene(frame):
    """
    frame: OpenCV BGR frame
    return: text description
    """

    # Convert OpenCV frame (BGR) → PIL Image (RGB)
    image = Image.fromarray(frame[:, :, ::-1])

    prompt = (
        "You are an assistive AI for visually impaired people. "
        "Describe the scene clearly and briefly. "
        "Mention obstacles, people, vehicles, and safe directions if visible."
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[image, prompt]
    )

    return response.text
