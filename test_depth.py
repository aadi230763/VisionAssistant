#!/usr/bin/env python3
"""
Depth Estimation Test Script

This script captures a single frame and shows detailed depth information
to verify MiDaS is working correctly.
"""

import cv2
import numpy as np
from depth_estimator import initialize_depth_model, estimate_depth, get_distance_bucket
from yolo_detector import YoloDetector

def test_depth():
    print("="*70)
    print("DEPTH ESTIMATION TEST")
    print("="*70)
    
    # Initialize depth model
    print("\n[1] Initializing MiDaS depth model...")
    success = initialize_depth_model("midas_small")
    if not success:
        print("❌ Failed to initialize depth model!")
        return
    print("✅ Depth model loaded successfully\n")
    
    # Initialize YOLO
    print("[2] Initializing YOLO detector...")
    detector = YoloDetector(model="yolo11s.pt", conf=0.35)
    print("✅ YOLO loaded successfully\n")
    
    # Capture frame
    print("[3] Opening camera...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Failed to open camera!")
        return
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ Failed to capture frame!")
        return
    print(f"✅ Frame captured: {frame.shape}\n")
    
    # Estimate depth
    print("[4] Estimating depth map...")
    depth_map = estimate_depth(frame)
    if depth_map is None:
        print("❌ Depth estimation failed!")
        return
    print(f"✅ Depth map generated: {depth_map.shape}\n")
    
    # Show depth statistics
    print("="*70)
    print("DEPTH MAP STATISTICS")
    print("="*70)
    print(f"Shape:      {depth_map.shape}")
    print(f"Min:        {depth_map.min():.4f} (closest point)")
    print(f"Max:        {depth_map.max():.4f} (farthest point)")
    print(f"Mean:       {depth_map.mean():.4f}")
    print(f"Median:     {np.median(depth_map):.4f}")
    print(f"Std Dev:    {depth_map.std():.4f}")
    
    # Show depth buckets distribution
    very_close = (depth_map < 0.25).sum()
    close = ((depth_map >= 0.25) & (depth_map < 0.45)).sum()
    moderate = ((depth_map >= 0.45) & (depth_map < 0.70)).sum()
    far = (depth_map >= 0.70).sum()
    total = depth_map.size
    
    print("\n" + "="*70)
    print("DISTANCE BUCKET DISTRIBUTION")
    print("="*70)
    print(f"Very Close (< 0.25):  {very_close:>8} pixels ({very_close/total*100:>5.2f}%)")
    print(f"Close (0.25-0.45):    {close:>8} pixels ({close/total*100:>5.2f}%)")
    print(f"Moderate (0.45-0.70): {moderate:>8} pixels ({moderate/total*100:>5.2f}%)")
    print(f"Far (> 0.70):         {far:>8} pixels ({far/total*100:>5.2f}%)")
    
    # Detect objects
    print("\n[5] Running YOLO detection with depth...")
    detections = detector.detect(frame, depth_map=depth_map)
    
    if not detections:
        print("No objects detected!")
        return
    
    print(f"\n✅ Detected {len(detections)} objects\n")
    
    # Show detailed object information
    print("="*70)
    print("DETECTED OBJECTS WITH DEPTH")
    print("="*70)
    print(f"{'Object':<15} {'Conf':<6} {'Depth':<8} {'Bucket':<12} {'Direction':<10}")
    print("-"*70)
    
    for d in detections:
        label = d.get('label', 'unknown')
        conf = d.get('confidence', 0.0)
        depth_val = d.get('depth_value', None)
        distance = d.get('distance', 'unknown')
        direction = d.get('direction', 'unknown')
        
        if depth_val is not None:
            print(f"{label:<15} {conf:<6.2f} {depth_val:<8.4f} {distance:<12} {direction:<10}")
        else:
            print(f"{label:<15} {conf:<6.2f} {'N/A':<8} {distance:<12} {direction:<10}")
    
    print("\n" + "="*70)
    print("INTERPRETATION GUIDE")
    print("="*70)
    print("Depth Values (normalized 0-1):")
    print("  0.00 - 0.25  →  VERY CLOSE (within arm's reach)")
    print("  0.25 - 0.45  →  CLOSE (a few steps away)")
    print("  0.45 - 0.70  →  MODERATE (several steps away)")
    print("  0.70 - 1.00  →  FAR (not immediate concern)")
    print("\nIf you see varying depth values for objects, MiDaS is working! ✅")
    print("="*70)

if __name__ == "__main__":
    test_depth()
