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
    """Format detection results for the AI prompt with depth information."""
    if not detections:
        return "No objects detected."
    
    lines: list[str] = []
    for d in detections[:max_items]:
        label = str(d.get("label", "object")).strip() or "object"
        conf = float(d.get("confidence", 0.0))
        
        # Add depth information if available
        distance = d.get("distance")
        direction = d.get("direction")
        
        if distance and direction:
            lines.append(f"- {label.title()} ({direction}, {distance})")
        else:
            lines.append(f"- {label.title()}")
    
    return "\n".join(lines)


def _format_ani_assessments(assessments: list[dict[str, Any]]) -> str:
    """Format ANI risk assessments for the AI prompt (anticipatory mode)."""
    if not assessments:
        return "No moving objects or risks detected."
    
    lines: list[str] = []
    for a in assessments:
        label = str(a.get("label", "object")).strip() or "object"
        direction = a.get("direction", "unknown")
        distance = a.get("distance", "unknown")
        motion = a.get("motion", "stationary")
        risk = a.get("risk", "low")
        
        # Format: "Person (ahead, close) - approaching - RISK: HIGH"
        lines.append(
            f"- {label.title()} ({direction}, {distance}) - {motion} - RISK: {risk.upper()}"
        )
    
    return "\n".join(lines)


def _has_very_close_hazard(detections: list[dict[str, Any]]) -> bool:
    """Check if any detection is very close and safety-relevant."""
    from depth_estimator import is_safety_relevant
    
    for d in detections:
        if d.get("distance") == "very_close" and is_safety_relevant(d.get("label", "")):
            return True
    return False


def _has_imminent_risk(assessments: list[dict[str, Any]]) -> bool:
    """Check if any ANI assessment indicates imminent risk."""
    return any(a.get("risk") == "imminent" for a in assessments)


def describe_scene(
    detections: list[dict[str, Any]],
    *,
    ani_assessments: Optional[list[dict[str, Any]]] = None,
    timeout_s: float = 12.0,
    retries: int = 2,
) -> Optional[str]:
    """
    Generate a natural language scene description from YOLO detections.
    
    Designed for visually impaired users: calm, concise, safety-focused narration.
    
    Args:
        detections: List of YOLO detection dicts with 'label' and 'confidence' keys
        ani_assessments: Optional ANI risk assessments (anticipatory mode)
        timeout_s: Maximum time to wait for response
        retries: Number of retry attempts on transient errors
    
    Returns:
        A short, spoken-friendly scene description, or None on error/no meaningful change
    """
    if not detections:
        return None
    
    # Determine mode: ANI (anticipatory) or standard
    use_ani = ani_assessments is not None and len(ani_assessments) > 0
    
    # Check for very close hazards (SAFETY OVERRIDE)
    has_urgent_hazard = _has_very_close_hazard(detections) if not use_ani else _has_imminent_risk(ani_assessments)
    
    # Check for emergency situations (high priority)
    emergency_objects = {
        'car', 'truck', 'bus', 'motorcycle', 'vehicle',
        'bicycle', 'traffic light', 'stop sign'
    }
    
    detected_labels = {d.get('label', '').lower() for d in detections}
    has_emergency = bool(detected_labels & emergency_objects)
    
    # Upgrade to emergency if very close hazard
    if has_urgent_hazard:
        has_emergency = True
    
    # Build the prompt - optimized for actionable navigation guidance
    if use_ani:
        # ANI MODE: Anticipatory, motion-aware guidance
        if has_urgent_hazard:
            # Imminent risk detected by ANI
            prompt = (
                "You are an assistive AI for visually impaired people with PREDICTIVE safety intelligence.\n"
                "IMMINENT collision risk detected based on object motion. Provide IMMEDIATE anticipatory guidance.\n\n"
                "URGENT RULES:\n"
                "1. Start with 'Warning' or 'Caution'\n"
                "2. Use predictive language: 'approaching', 'about to cross', 'moving toward you'\n"
                "3. State object, direction, and motion\n"
                "4. Give ONE immediate action: 'Stop', 'Step back', 'Pause'\n"
                "5. Be firm but calm - this is predicted danger\n"
                "6. Maximum 2 sentences\n\n"
                "MOTION TYPES:\n"
                "- approaching: Moving toward you\n"
                "- crossing: Moving across your path\n"
                "- moving: In motion but not toward you\n"
                "- stationary: Not moving\n\n"
                "RISK LEVELS:\n"
                "- IMMINENT: Collision likely within 1-2 seconds\n"
                "- HIGH: Significant risk if you continue\n"
                "- MEDIUM: Potential risk, proceed with caution\n\n"
                "EXAMPLES:\n"
                "- 'Warning. Person approaching directly ahead. Please stop and wait.'\n"
                "- 'Caution. Bicycle crossing from the left. Pause briefly.'\n"
                "- 'Warning. Vehicle approaching from your right. Step back immediately.'\n\n"
                f"Motion-based risk assessments:\n{_format_ani_assessments(ani_assessments)}\n\n"
                "Provide urgent anticipatory guidance:"
            )
        else:
            # Normal ANI mode with motion awareness
            prompt = (
                "You are an assistive AI for visually impaired people with ANTICIPATORY intelligence.\n"
                "Provide proactive navigation guidance based on predicted object motion.\n\n"
                "ANTICIPATORY RULES:\n"
                "1. Focus on objects in motion, not static environment\n"
                "2. Use predictive language when appropriate:\n"
                "   - 'approaching' for objects moving toward you\n"
                "   - 'crossing your path' for lateral motion\n"
                "   - 'moving away' for objects leaving\n"
                "3. Provide anticipatory suggestions:\n"
                "   - 'slow down' if medium risk ahead\n"
                "   - 'keep left/right' to avoid crossing objects\n"
                "   - 'pause briefly' if path may clear\n"
                "4. Be calm and reassuring\n"
                "5. Maximum 2 sentences\n\n"
                "MOTION AWARENESS:\n"
                "- approaching: 'A person is approaching from ahead. Slow down.'\n"
                "- crossing: 'Someone is about to cross from your left. Keep slightly right.'\n"
                "- moving: 'A cyclist is moving on your right. Maintain your path.'\n\n"
                f"Motion-based assessments:\n{_format_ani_assessments(ani_assessments)}\n\n"
                "Provide anticipatory guidance:"
            )
    elif has_emergency:
        # Emergency mode: Immediate danger warning with action command
        prompt = (
            "You are an assistive AI for visually impaired people. "
            "An emergency hazard has been detected. Provide IMMEDIATE safety guidance.\n\n"
            "URGENT RULES:\n"
            "1. Start with 'Warning' or 'Caution'\n"
            "2. State the object type and location (left/right/ahead)\n"
            "3. Give ONE clear action: 'Step back', 'Stop', 'Move right'\n"
            "4. If distance is 'very_close', emphasize urgency\n"
            "5. Use approximate language: 'very close', 'right beside you', 'immediately ahead'\n"
            "6. Be firm but calm\n"
            "7. Maximum 2 short sentences\n\n"
            "DISTANCE MEANINGS:\n"
            "- very_close: Within arm's reach, immediate danger\n"
            "- close: A few steps away\n"
            "- moderate: Several steps away\n"
            "- far: Not an immediate concern\n\n"
            "EXAMPLES:\n"
            "- 'Warning. Vehicle very close on your right. Step back immediately.'\n"
            "- 'Caution. Person directly ahead, very close. Please stop.'\n"
            "- 'Warning. Bicycle approaching from the left. Stop and wait.'\n\n"
            f"Detected objects:\n{_format_detections(detections)}\n\n"
            "Provide urgent safety guidance:"
        )
    else:
        # Normal mode: decisive, actionable guidance with distance awareness
        prompt = (
            "You are an assistive AI for visually impaired people. "
            "Your role is to provide decisive, actionable navigation guidance.\n\n"
            "CRITICAL RULES:\n"
            "1. Use directional language: left/right, ahead/behind\n"
            "2. Convert distance categories into approximate language:\n"
            "   - very_close → 'very close', 'right beside you', 'within arm's reach'\n"
            "   - close → 'a few steps away', 'nearby'\n"
            "   - moderate → 'several steps ahead'\n"
            "   - far → mention only if safety-relevant\n"
            "3. When obstacles are close or very_close, suggest ONE specific direction to avoid them\n"
            "4. Be decisive: 'Move slightly right' not 'move left or right'\n"
            "5. NEVER say exact distances in meters or feet\n"
            "6. Keep it to 1-2 sentences maximum\n"
            "7. Be calm and reassuring\n\n"
            "EXAMPLES OF GOOD GUIDANCE:\n"
            "- 'A person is a few steps ahead on the left. Move slightly right.'\n"
            "- 'There is a chair very close on your left. Please stop and step right.'\n"
            "- 'The path ahead is clear. You can walk forward safely.'\n"
            "- 'A table is nearby, slightly ahead. Keep to the left depending on space.'\n\n"
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
