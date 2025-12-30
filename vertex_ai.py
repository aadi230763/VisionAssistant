"""
Vertex AI Scene Description Module for Vision-to-Voice Assistant

Uses Google Cloud Vertex AI with Gemini models to generate natural language
scene descriptions from YOLO object detections. Optimized for visually impaired users.

Authentication: Uses Application Default Credentials (ADC) - no API key required.
"""

import os
import time
from typing import Any, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()

# Configuration
VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
VERTEX_MODEL = os.getenv("VERTEX_MODEL", "gemini-2.0-flash-exp")

# Initialize client (lazy initialization on first use)
_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    """Get or create the Vertex AI client using ADC."""
    global _client
    if _client is None:
        if not VERTEX_PROJECT_ID:
            raise RuntimeError(
                "VERTEX_PROJECT_ID is not set. Please configure .env file."
            )
        _client = genai.Client(
            vertexai=True,
            project=VERTEX_PROJECT_ID,
            location=VERTEX_LOCATION,
        )
    return _client


def _format_detections(detections: list[dict[str, Any]], max_items: int = 10) -> str:
    """Format detection results for the AI prompt."""
    if not detections:
        return "No objects detected."
    
    lines: list[str] = []
    for d in detections[:max_items]:
        label = str(d.get("label", "object")).strip() or "object"
        conf = float(d.get("confidence", 0.0))
        lines.append(f"- {label.title()} ({int(conf * 100)}%)")
    
    return "\n".join(lines)


def describe_scene(
    detections: list[dict[str, Any]],
    *,
    timeout_s: float = 12.0,
    retries: int = 2,
) -> Optional[str]:
    """
    Generate a natural language scene description from YOLO detections.
    
    Designed for visually impaired users: calm, concise, safety-focused narration.
    
    Args:
        detections: List of YOLO detection dicts with 'label' and 'confidence' keys
        timeout_s: Maximum time to wait for response
        retries: Number of retry attempts on transient errors
    
    Returns:
        A short, spoken-friendly scene description, or None on error/no meaningful change
    """
    if not detections:
        return None
    
    # Check for emergency situations (high priority)
    emergency_objects = {
        'car', 'truck', 'bus', 'motorcycle', 'vehicle',
        'bicycle', 'traffic light', 'stop sign'
    }
    
    detected_labels = {d.get('label', '').lower() for d in detections}
    has_emergency = bool(detected_labels & emergency_objects)
    
    # Build the prompt - optimized for actionable navigation guidance
    if has_emergency:
        # Emergency mode: urgent, directive warning
        prompt = (
            "URGENT: You are providing emergency navigation guidance to a visually impaired person.\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Start with 'Warning.' or 'Caution.'\n"
            "2. State the danger clearly (vehicle, moving object, hazard)\n"
            "3. Give ONE immediate action: Stop, Step back, Stay still, Move aside\n"
            "4. Be firm but calm\n"
            "5. Maximum 2 short sentences\n\n"
            "EXAMPLES:\n"
            "- 'Warning. Vehicle approaching. Please stop immediately.'\n"
            "- 'Caution. Car very close on your right. Step back and wait.'\n"
            "- 'Warning. Bicycle ahead. Stop and let it pass.'\n\n"
            f"Detected objects:\n{_format_detections(detections)}\n\n"
            "Provide urgent safety guidance:"
        )
    else:
        # Normal mode: decisive, actionable guidance
        prompt = (
            "You are an assistive AI for visually impaired people. "
            "Your role is to provide decisive, actionable navigation guidance.\n\n"
            "CRITICAL RULES:\n"
            "1. Always use directional language: left/right, ahead/behind, near/far\n"
            "2. Use distance estimates: one step, two steps, a few steps, close by, nearby\n"
            "3. When obstacles are present, suggest ONE specific direction (not 'left or right' - choose one)\n"
            "4. Be decisive: 'Move slightly right' not 'move left or right depending on space'\n"
            "5. Keep it to 1-2 sentences maximum\n"
            "6. Be calm and reassuring\n\n"
            "EXAMPLES OF DECISIVE GUIDANCE:\n"
            "- 'A person is ahead and a chair is to your left. Move one step right.'\n"
            "- 'There is a table slightly ahead. Keep left to avoid it.'\n"
            "- 'The path ahead is clear. You can walk forward safely.'\n"
            "- 'A bottle is on the ground two steps ahead. Step to the right.'\n\n"
            f"Detected objects:\n{_format_detections(detections)}\n\n"
            "Provide decisive navigation guidance:"
        )
    
    # Retry loop with exponential backoff
    last_err: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            client = _get_client()
            
            response = client.models.generate_content(
                model=VERTEX_MODEL,
                contents=prompt,
                config={
                    "temperature": 0.3 if has_emergency else 0.4,  # More consistent for emergencies
                    "max_output_tokens": 80 if has_emergency else 100,
                }
            )
            
            # Extract and clean text
            if response and hasattr(response, 'text'):
                text = (response.text or "").strip().strip('"').strip("'")
                return text if text else None
            
            return None
            
        except errors.ClientError as e:
            # Handle 4xx errors (don't retry)
            if hasattr(e, 'status_code') and e.status_code and 400 <= e.status_code < 500:
                print(f"[vertex] client error: {e.status_code}")
                return None
            last_err = e
            
        except errors.ServerError:
            # Handle 5xx errors (retry)
            last_err = errors.ServerError
            
        except Exception as e:
            # Unexpected errors
            last_err = e
        
        # Exponential backoff before retry
        if attempt < retries:
            time.sleep(0.5 * (2 ** attempt))
    
    # All retries exhausted
    if last_err:
        print(f"[vertex] error after {retries + 1} attempts: {last_err}")
    return None
