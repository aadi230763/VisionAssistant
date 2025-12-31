"""
WebSocket server to stream Vision Assistant data to the UI dashboard.
"""

import asyncio
import json
import base64
import cv2
import websockets
from typing import Set
import os
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


async def handle_client(websocket):
    """Handle WebSocket client connection."""
    connected_clients.add(websocket)
    print(f"📱 Client connected. Total: {len(connected_clients)}")
    
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)
        print(f"📱 Client disconnected. Total: {len(connected_clients)}")


async def broadcast_frame(data):
    """Send data to all connected clients."""
    if connected_clients:
        message = json.dumps(data)
        await asyncio.gather(
            *[client.send(message) for client in connected_clients],
            return_exceptions=True
        )


async def process_camera_stream():
    """Process camera and broadcast to UI."""
    print("📹 Starting camera stream...")
    camera_index = int(os.getenv("CAMERA_INDEX", "0"))
    frame_count = 0
    
    for frame in get_frames(camera_index):
        frame_count += 1
        
        if frame_count % 5 != 0:  # Process every 5th frame for better detection
            continue
        
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
            
            # Generate comprehensive guidance based on all detected objects
            very_close = [o for o in ui_objects if o['distance'] == 'very_close']
            close = [o for o in ui_objects if o['distance'] == 'close']
            
            if very_close:
                if len(very_close) == 1:
                    obj = very_close[0]
                    guidance = f"Warning! {obj['label'].capitalize()} very close {obj['direction']}. Stop immediately."
                else:
                    directions = ', '.join(set(o['direction'] for o in very_close[:3]))
                    guidance = f"Warning! Multiple objects very close: {directions}. Stop now!"
            elif close:
                if len(close) == 1:
                    obj = close[0]
                    guidance = f"{obj['label'].capitalize()} close {obj['direction']}. Slow down and proceed with caution."
                else:
                    # List multiple close objects
                    objects_desc = ', '.join(f"{o['label']} {o['direction']}" for o in close[:3])
                    guidance = f"Multiple objects nearby: {objects_desc}. Move carefully."
            elif len(ui_objects) >= 3:
                guidance = f"Detecting {len(ui_objects)} objects in environment. Stay alert."
        
        # Broadcast
        await broadcast_frame({
            'frame': frame_b64,
            'objects': ui_objects,
            'spoken_guidance': guidance,
            'thinking': False
        })
        
        await asyncio.sleep(0.1)


async def main():
    """Start WebSocket server."""
    server = await websockets.serve(handle_client, "localhost", 8765)
    print("🌐 WebSocket server on ws://localhost:8765")
    
    camera_task = asyncio.create_task(process_camera_stream())
    
    await asyncio.gather(server.wait_closed(), camera_task)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
