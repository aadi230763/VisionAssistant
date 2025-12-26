from google import genai
import os
from dotenv import load_dotenv

load_dotenv()  # 👈 THIS IS IMPORTANT

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

models = client.models.list()

print("\nAvailable models:\n")
for m in models:
    print("-", m.name)
