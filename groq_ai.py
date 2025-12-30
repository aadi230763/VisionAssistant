"""
DEPRECATED: This module is no longer used in the main application.
The system now uses Vertex AI (vertex_ai.py) as the primary reasoning model.

This file is kept for reference only.
"""

import os
import time
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def _format_detections(detections: list[dict[str, Any]], max_items: int = 10) -> str:
    lines: list[str] = []
    for d in detections[:max_items]:
        label = str(d.get("label", "object")).strip() or "object"
        conf = float(d.get("confidence", 0.0))
        lines.append(f"- {label.title()} ({int(conf * 100)}%)")
    return "\n".join(lines)


def describe_scene(
    detections: list[dict[str, Any]],
    *,
    timeout_s: float = 15.0,
    retries: int = 2,
) -> str | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    if not detections:
        return None

    prompt = (
        "You are assisting a visually impaired user. "
        "Describe the scene clearly and concisely in one short sentence. "
        "Avoid listing percentages. If you are unsure, be cautious.\n"
        "Detected objects:\n"
        f"{_format_detections(detections)}"
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You convert detections into spoken scene descriptions."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 80,
    }

    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=(3.05, timeout_s),
            )

            if 500 <= resp.status_code < 600:
                raise RuntimeError(f"Groq server error: {resp.status_code}")
            if resp.status_code >= 400:
                raise RuntimeError(f"Groq request failed: {resp.status_code} {resp.text}")

            data = resp.json()
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            content = (content or "").strip().strip('"').strip("'")
            return content or None
        except Exception as exc:
            last_err = exc
            if attempt >= retries:
                break
            time.sleep(0.5 * (2**attempt))

    print(f"[groq] error: {last_err}")
    return None
