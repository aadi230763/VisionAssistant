"""
Depth Estimator Module for Vision-to-Voice Assistant

Uses monocular depth estimation to provide relative distance information
for detected objects. Enhances spatial awareness without claiming precision.
"""

import os
from typing import Optional

import cv2
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# Distance bucket thresholds (normalized 0-1, where 0=close, 1=far)
VERY_CLOSE_THRESHOLD = 0.25
CLOSE_THRESHOLD = 0.45
MODERATE_THRESHOLD = 0.70
# Above MODERATE_THRESHOLD = FAR

_model: Optional[object] = None
_model_type: Optional[str] = None


def _load_midas_small():
    """Load MiDaS small model (lightweight, good for CPU)."""
    import torch
    
    model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small", trust_repo=True)
    model.eval()
    
    # Move to GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    
    # Get transform
    midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True)
    transform = midas_transforms.small_transform
    
    return model, transform, device


def initialize_depth_model(model_type: str = "midas_small"):
    """
    Initialize the depth estimation model.
    
    Args:
        model_type: Type of model to use ("midas_small" recommended)
    
    Returns:
        True if successful, False otherwise
    """
    global _model, _model_type
    
    try:
        print(f"[depth] Loading {model_type} model...")
        
        if model_type == "midas_small":
            _model, _transform, _device = _load_midas_small()
            _model_type = model_type
            print(f"[depth] Model loaded successfully on {_device}")
            return True
        else:
            print(f"[depth] Unknown model type: {model_type}")
            return False
            
    except Exception as e:
        print(f"[depth] Failed to load model: {e}")
        _model = None
        _model_type = None
        return False


def estimate_depth(frame: np.ndarray) -> Optional[np.ndarray]:
    """
    Estimate depth map from a single frame.
    
    Args:
        frame: Input frame (BGR format from OpenCV)
    
    Returns:
        Normalized depth map (0=close, 1=far) or None on failure
    """
    global _model, _model_type
    
    if _model is None:
        return None
    
    try:
        import torch
        
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Apply transform and prepare batch
        if _model_type == "midas_small":
            # Get transform (stored during initialization)
            midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True)
            transform = midas_transforms.small_transform
            
            input_batch = transform(img_rgb)
            
            # Move to device
            device = next(_model.parameters()).device
            input_batch = input_batch.to(device)
            
            # Predict depth
            with torch.no_grad():
                prediction = _model(input_batch)
                prediction = torch.nn.functional.interpolate(
                    prediction.unsqueeze(1),
                    size=img_rgb.shape[:2],
                    mode="bicubic",
                    align_corners=False,
                ).squeeze()
            
            # Convert to numpy
            depth_map = prediction.cpu().numpy()
            
            # Normalize to 0-1 (invert so 0=close, 1=far)
            depth_map = depth_map - depth_map.min()
            depth_map = depth_map / (depth_map.max() + 1e-8)
            depth_map = 1.0 - depth_map  # Invert: 0=far, 1=close → 0=close, 1=far
            
            return depth_map
            
    except Exception as e:
        print(f"[depth] Estimation failed: {e}")
        return None


def get_distance_bucket(depth_value: float) -> str:
    """
    Convert normalized depth value to distance bucket.
    
    Args:
        depth_value: Normalized depth (0=close, 1=far)
    
    Returns:
        Distance bucket string
    """
    if depth_value < VERY_CLOSE_THRESHOLD:
        return "very_close"
    elif depth_value < CLOSE_THRESHOLD:
        return "close"
    elif depth_value < MODERATE_THRESHOLD:
        return "moderate"
    else:
        return "far"


def compute_bbox_depth(depth_map: np.ndarray, bbox: tuple) -> tuple[float, str]:
    """
    Compute representative depth for a bounding box region.
    
    Args:
        depth_map: Normalized depth map (0=close, 1=far)
        bbox: Bounding box as (x1, y1, x2, y2)
    
    Returns:
        (median_depth, distance_bucket)
    """
    x1, y1, x2, y2 = bbox
    
    # Ensure coordinates are within bounds
    h, w = depth_map.shape
    x1, y1 = max(0, int(x1)), max(0, int(y1))
    x2, y2 = min(w, int(x2)), min(h, int(y2))
    
    # Extract region
    region = depth_map[y1:y2, x1:x2]
    
    if region.size == 0:
        return 0.5, "moderate"  # Fallback
    
    # Use median (robust to outliers)
    median_depth = float(np.median(region))
    bucket = get_distance_bucket(median_depth)
    
    return median_depth, bucket


def get_object_direction(bbox: tuple, frame_width: int) -> str:
    """
    Determine horizontal direction of object relative to camera center.
    
    Args:
        bbox: Bounding box as (x1, y1, x2, y2)
        frame_width: Width of the frame
    
    Returns:
        Direction string: "left", "right", or "ahead"
    """
    x1, y1, x2, y2 = bbox
    center_x = (x1 + x2) / 2
    frame_center = frame_width / 2
    
    # Thresholds for left/right (20% margin from center)
    left_threshold = frame_width * 0.4
    right_threshold = frame_width * 0.6
    
    if center_x < left_threshold:
        return "left"
    elif center_x > right_threshold:
        return "right"
    else:
        return "ahead"


def is_safety_relevant(label: str) -> bool:
    """
    Check if object is safety-relevant regardless of distance.
    
    Args:
        label: Object label
    
    Returns:
        True if safety-relevant
    """
    safety_labels = {
        'person', 'car', 'truck', 'bus', 'motorcycle', 'bicycle',
        'chair', 'couch', 'bench', 'stairs', 'traffic light', 'stop sign'
    }
    return label.lower() in safety_labels
