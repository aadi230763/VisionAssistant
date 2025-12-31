"""
WebSocket server to stream Vision Assistant data to the UI dashboard.
"""

import asyncio
import json
import base64
import cv2
import numpy as np
import websockets
from typing import Set
import os
import time
from collections import defaultdict
from dotenv import load_dotenv

from camera import get_frames
from yolo_detector import YoloDetector
from depth_estimator import initialize_depth_model, estimate_depth

load_dotenv()

connected_clients: Set[websockets.WebSocketServerProtocol] = set()

# Initialize models
print("🔧 Initializing models for UI stream...")
depth_enabled = initialize_depth_model("midas_small")
detector = YoloDetector(
    model=os.getenv("YOLO_MODEL", "yolo11s.pt"),
    conf=float(os.getenv("YOLO_CONF", "0.35"))
)
print("✅ Models ready")

# Tracking state for 10-second summaries
last_guidance_time = 0
GUIDANCE_INTERVAL = 10.0  # seconds
accumulated_detections = []
client_frames = {}  # Store frames from browser clients


async def handle_client(websocket):
    """Handle WebSocket client connection and receive frames from browser."""
    connected_clients.add(websocket)
    client_id = id(websocket)
    print(f"📱 Client connected. Total: {len(connected_clients)}")
    
    try:
        async for message in websocket:
            # Receive frames from browser camera
            data = json.loads(message)
            if data.get('type') == 'frame':
                # Store the frame for processing
                client_frames[client_id] = data.get('frame')
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        connected_clients.remove(websocket)
        if client_id in client_frames:
            del client_frames[client_id]
        print(f"📱 Client disconnected. Total: {len(connected_clients)}")


async def broadcast_frame(data):
    """Send data to all connected clients."""
    if connected_clients:
        message = json.dumps(data)
        await asyncio.gather(
            *[client.send(message) for client in connected_clients],
            return_exceptions=True
        )


async def generate_summary_guidance(detections_over_time):
    """Generate a comprehensive 10-second summary of the environment."""
    if not detections_over_time:
        return "Environment clear. Safe to proceed."
    
    # Aggregate all detections from the 10-second window
    all_objects = []
    for detection_set in detections_over_time:
        for obj in detection_set:
            all_objects.append(obj)
    
    # Remove duplicates by keeping closest detection for each position
    # (but keep multiple instances of same label if in different positions)
    unique_objects = []
    for obj in all_objects:
        # Check if similar object already exists (same label, similar direction, similar distance)
        is_duplicate = False
        for existing in unique_objects:
            if (existing['label'] == obj['label'] and 
                existing['direction'] == obj['direction'] and 
                existing['distance'] == obj['distance']):
                is_duplicate = True
                break
        if not is_duplicate:
            unique_objects.append(obj)
    
    # Categorize by risk
    very_close = [o for o in unique_objects if o['distance'] == 'very_close']
    close = [o for o in unique_objects if o['distance'] == 'close']
    moderate = [o for o in unique_objects if o['distance'] == 'moderate']
    
    # Count people specifically
    people_very_close = [o for o in very_close if o['label'] == 'person']
    people_close = [o for o in close if o['label'] == 'person']
    
    # Build comprehensive summary
    summary_parts = []
    
    # Critical warnings first
    if very_close:
        if len(people_very_close) > 1:
            directions = ', '.join(set(o['direction'] for o in people_very_close[:3]))
            summary_parts.append(f"Danger! {len(people_very_close)} people very close at {directions}. Stop now")
        elif len(very_close) == 1:
            obj = very_close[0]
            summary_parts.append(f"Danger! {obj['label']} very close {obj['direction']}. Stop now")
        else:
            items = ', '.join(o['label'] for o in very_close[:2])
            summary_parts.append(f"Danger! {items} very close. Stop immediately")
    
    # Close objects
    if close:
        if len(people_close) > 1:
            summary_parts.append(f"{len(people_close)} people nearby")
        elif len(close) == 1:
            obj = close[0]
            summary_parts.append(f"{obj['label']} close {obj['direction']}")
        elif len(close) == 2:
            summary_parts.append(f"{close[0]['label']} and {close[1]['label']} close")
        else:
            summary_parts.append(f"{len(close)} objects nearby")
    
    # Moderate distance awareness
    if moderate and not very_close and not close:
        people_moderate = [o for o in moderate if o['label'] == 'person']
        if len(people_moderate) > 1:
            summary_parts.append(f"{len(people_moderate)} people detected at safe distance")
        elif len(moderate) == 1:
            summary_parts.append(f"{moderate[0]['label']} ahead at moderate distance")
        else:
            summary_parts.append(f"{len(moderate)} objects detected at safe distance")
    
    # Overall safety assessment
    if very_close:
        summary_parts.append("Proceed with extreme caution")
    elif close:
        summary_parts.append("Slow down and be careful")
    elif moderate:
        summary_parts.append("Environment safe, stay alert")
    else:
        summary_parts.append("All clear")
    
    return '. '.join(summary_parts) + '.'


async def process_browser_frames():
    """Process frames from browser cameras."""
    global last_guidance_time, accumulated_detections
    
    print("📹 Ready to process browser camera frames...")
    frame_count = 0
    
    while True:
        if not client_frames:
            await asyncio.sleep(0.1)
            continue
        
        # Get the most recent frame from any connected client
        frame_b64 = list(client_frames.values())[0]
        
        try:
            # Decode base64 frame from browser
            frame_data = base64.b64decode(frame_b64.split(',')[1] if ',' in frame_b64 else frame_b64)
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                await asyncio.sleep(0.1)
                continue
            
            frame_count += 1
            if frame_count % 5 != 0:  # Process every 5th frame
                await asyncio.sleep(0.033)
                continue
            
            current_time = time.time()
            
            # Detect with depth
            depth_map = estimate_depth(frame) if depth_enabled else None
            detections = detector.detect(frame, depth_map=depth_map)
            
            # Prepare UI objects
            ui_objects = []
            guidance = ""
            
            if detections:
                for det in detections[:8]:  # Show up to 8 objects
                    risk = 'imminent' if det.get('distance') == 'very_close' else \
                           'high' if det.get('distance') == 'close' else \
                           'medium' if det.get('distance') == 'moderate' else 'low'
                    
                    ui_objects.append({
                        'label': det['label'],
                        'distance': det.get('distance', 'moderate'),
                        'direction': det.get('direction', 'ahead'),
                        'motion': 'stationary',
                        'risk': risk,
                        'bbox': det.get('bbox')
                    })
                
                # Accumulate detections for summary
                accumulated_detections.append(ui_objects)
            
            # Generate guidance summary every 10 seconds
            time_since_last = current_time - last_guidance_time
            if time_since_last >= GUIDANCE_INTERVAL:
                guidance = await generate_summary_guidance(accumulated_detections)
                last_guidance_time = current_time
                accumulated_detections = []  # Reset for next interval
                print(f"🔊 Summary: {guidance}")
            
            # Encode and send back
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            processed_frame_b64 = base64.b64encode(buffer).decode('utf-8')
            
            # Broadcast
            await broadcast_frame({
                'frame': processed_frame_b64,
                'objects': ui_objects,
                'spoken_guidance': guidance,
                'thinking': False
            })
            
        except Exception as e:
            print(f"Error processing frame: {e}")
        
        await asyncio.sleep(0.033)  # ~30 FPS


async def process_camera_stream():
    """Process camera and broadcast to UI - FALLBACK for local/demo mode."""
    global last_guidance_time, accumulated_detections
    
    print("📹 Starting camera stream...")
    camera_index = int(os.getenv("CAMERA_INDEX", "0"))
    frame_count = 0
    
    for frame in get_frames(camera_index):
        frame_count += 1
        
        if frame_count % 5 != 0:  # Process every 5th frame for better detection
            continue
        
        current_time = time.time()
        
        # Encode frame
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        frame_b64 = base64.b64encode(buffer).decode('utf-8')
        
        # Detect with depth
        depth_map = estimate_depth(frame) if depth_enabled else None
        detections = detector.detect(frame, depth_map=depth_map)
        
        # Prepare UI objects
        ui_objects = []
        guidance = ""
        
        if detections:
            for det in detections[:8]:  # Show up to 8 objects
                risk = 'imminent' if det.get('distance') == 'very_close' else \
                       'high' if det.get('distance') == 'close' else \
                       'medium' if det.get('distance') == 'moderate' else 'low'
                
                ui_objects.append({
                    'label': det['label'],
                    'distance': det.get('distance', 'moderate'),
                    'direction': det.get('direction', 'ahead'),
                    'motion': 'stationary',
                    'risk': risk,
                    'bbox': det.get('bbox')
                })
            
            # Accumulate detections for summary
            accumulated_detections.append(ui_objects)
        
        # Generate guidance summary every 3 seconds
        time_since_last = current_time - last_guidance_time
        if time_since_last >= GUIDANCE_INTERVAL:
            guidance = await generate_summary_guidance(accumulated_detections)
            last_guidance_time = current_time
            accumulated_detections = []  # Reset for next interval
            print(f"🔊 Summary: {guidance}")
        
        # Broadcast (only include guidance when it's time)
        await broadcast_frame({
            'frame': frame_b64,
            'objects': ui_objects,
            'spoken_guidance': guidance,
            'thinking': False
        })
        
        await asyncio.sleep(0.1)


async def main():
    """Start WebSocket server."""
    # Use browser camera mode if specified (for cloud deployment)
    use_browser_camera = os.getenv("USE_BROWSER_CAMERA", "true").lower() == "true"
    
    server = await websockets.serve(handle_client, "0.0.0.0", 8765)
    print("🌐 WebSocket server on ws://0.0.0.0:8765")
    
    if use_browser_camera:
        print("📱 Browser camera mode - waiting for client frames")
        camera_task = asyncio.create_task(process_browser_frames())
    else:
        print("🎥 Local camera mode - using device camera")
        camera_task = asyncio.create_task(process_camera_stream())
    
    await asyncio.gather(server.wait_closed(), camera_task)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
