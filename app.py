from camera import get_frames
from gemini_ai import analyze_scene
import time

print("🚀 Vision-to-Voice Assistant Started")

LAST_CALL = 0
INTERVAL = 10  # seconds (VERY IMPORTANT)

for frame in get_frames():
    now = time.time()

    if now - LAST_CALL < INTERVAL:
        continue  # skip frame

    LAST_CALL = now

    try:
        description = analyze_scene(frame)
        print("🧠 Scene:", description)
    except Exception as e:
        print("Error:", e)
