"""
Anticipatory Navigation Intelligence (ANI) Engine

Provides lightweight temporal tracking and motion prediction for proactive
safety guidance. Predicts near-future risk based on object motion.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


class TrackedObject:
    """Represents a tracked object with temporal history."""
    
    def __init__(self, object_id: int, detection: Dict[str, Any], timestamp: float):
        self.id = object_id
        self.label = detection.get('label', 'object')
        self.last_position: Optional[Tuple[float, float]] = None
        self.current_position = self._get_centroid(detection)
        self.last_timestamp: Optional[float] = None
        self.current_timestamp = timestamp
        self.velocity = (0.0, 0.0)  # pixels per second
        self.distance = detection.get('distance', 'moderate')
        self.direction = detection.get('direction', 'ahead')
        self.missed_frames = 0
        
    def _get_centroid(self, detection: Dict[str, Any]) -> Tuple[float, float]:
        """Extract centroid from detection (use bbox if available)."""
        bbox = detection.get('bbox')
        if bbox:
            x1, y1, x2, y2 = bbox
            return ((x1 + x2) / 2, (y1 + y2) / 2)
        # Fallback: use direction as approximate position
        direction = detection.get('direction', 'ahead')
        if direction == 'left':
            return (0.3, 0.5)
        elif direction == 'right':
            return (0.7, 0.5)
        else:  # ahead
            return (0.5, 0.5)
    
    def update(self, detection: Dict[str, Any], timestamp: float):
        """Update object state with new detection."""
        self.last_position = self.current_position
        self.last_timestamp = self.current_timestamp
        self.current_position = self._get_centroid(detection)
        self.current_timestamp = timestamp
        self.distance = detection.get('distance', self.distance)
        self.direction = detection.get('direction', self.direction)
        self.missed_frames = 0
        
        # Calculate velocity
        if self.last_position and self.last_timestamp:
            dt = timestamp - self.last_timestamp
            if dt > 0:
                dx = self.current_position[0] - self.last_position[0]
                dy = self.current_position[1] - self.last_position[1]
                self.velocity = (dx / dt, dy / dt)


class ANIEngine:
    """Anticipatory Navigation Intelligence Engine."""
    
    def __init__(
        self,
        max_tracking_distance: float = 0.3,  # Max distance for ID association
        max_missed_frames: int = 5,
        prediction_horizon_s: float = 1.5,  # Predict 1.5 seconds ahead
    ):
        self.tracked_objects: Dict[int, TrackedObject] = {}
        self.next_id = 0
        self.max_tracking_distance = max_tracking_distance
        self.max_missed_frames = max_missed_frames
        self.prediction_horizon_s = prediction_horizon_s
        
        # Safety-relevant object types
        self.safety_labels = {
            'person', 'car', 'truck', 'bus', 'motorcycle', 'bicycle',
            'dog', 'cat', 'skateboard', 'scooter'
        }
    
    def process_frame(
        self,
        detections: List[Dict[str, Any]],
        frame_width: int = 1920,
        frame_height: int = 1080
    ) -> List[Dict[str, Any]]:
        """
        Process detections and return anticipatory risk assessments.
        
        Args:
            detections: List of YOLO detections with optional depth info
            frame_width: Frame width for normalization
            frame_height: Frame height for normalization
        
        Returns:
            List of ANI assessments for risky objects
        """
        timestamp = time.time()
        
        # Update tracking
        self._update_tracking(detections, timestamp)
        
        # Generate risk assessments
        assessments = []
        for obj in self.tracked_objects.values():
            assessment = self._assess_risk(obj, frame_width, frame_height)
            if assessment:
                assessments.append(assessment)
        
        # Cleanup old tracks
        self._cleanup_tracks()
        
        return assessments
    
    def _update_tracking(self, detections: List[Dict[str, Any]], timestamp: float):
        """Update object tracking with new detections."""
        if not detections:
            # Increment missed frames for all tracks
            for obj in self.tracked_objects.values():
                obj.missed_frames += 1
            return
        
        # Convert detections to centroids
        detection_centroids = []
        for det in detections:
            bbox = det.get('bbox')
            if bbox:
                x1, y1, x2, y2 = bbox
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            else:
                # Fallback position based on direction
                direction = det.get('direction', 'ahead')
                if direction == 'left':
                    cx, cy = 0.3, 0.5
                elif direction == 'right':
                    cx, cy = 0.7, 0.5
                else:
                    cx, cy = 0.5, 0.5
            detection_centroids.append((cx, cy, det))
        
        # Match detections to existing tracks
        matched_tracks = set()
        matched_detections = set()
        
        for track_id, tracked_obj in list(self.tracked_objects.items()):
            best_match_idx = None
            best_distance = self.max_tracking_distance
            
            for idx, (cx, cy, det) in enumerate(detection_centroids):
                if idx in matched_detections:
                    continue
                
                # Only match same label
                if det.get('label') != tracked_obj.label:
                    continue
                
                # Calculate distance
                dist = np.sqrt(
                    (cx - tracked_obj.current_position[0])**2 +
                    (cy - tracked_obj.current_position[1])**2
                )
                
                if dist < best_distance:
                    best_distance = dist
                    best_match_idx = idx
            
            if best_match_idx is not None:
                # Update existing track
                _, _, det = detection_centroids[best_match_idx]
                tracked_obj.update(det, timestamp)
                matched_tracks.add(track_id)
                matched_detections.add(best_match_idx)
            else:
                # No match, increment missed frames
                tracked_obj.missed_frames += 1
        
        # Create new tracks for unmatched detections
        for idx, (cx, cy, det) in enumerate(detection_centroids):
            if idx not in matched_detections:
                new_obj = TrackedObject(self.next_id, det, timestamp)
                self.tracked_objects[self.next_id] = new_obj
                self.next_id += 1
    
    def _cleanup_tracks(self):
        """Remove stale tracks."""
        to_remove = []
        for track_id, obj in self.tracked_objects.items():
            if obj.missed_frames > self.max_missed_frames:
                to_remove.append(track_id)
        
        for track_id in to_remove:
            del self.tracked_objects[track_id]
    
    def _assess_risk(
        self,
        obj: TrackedObject,
        frame_width: int,
        frame_height: int
    ) -> Optional[Dict[str, Any]]:
        """
        Assess collision risk for a tracked object.
        
        Returns:
            ANI assessment dict or None if risk is negligible
        """
        # Skip if not safety-relevant
        if obj.label.lower() not in self.safety_labels:
            return None
        
        # Skip if no velocity data yet
        if obj.last_position is None:
            return None
        
        # Calculate motion characteristics
        velocity_magnitude = np.sqrt(obj.velocity[0]**2 + obj.velocity[1]**2)
        
        # Determine motion type
        motion = self._classify_motion(obj, velocity_magnitude)
        
        # Calculate risk level
        risk = self._calculate_risk(obj, velocity_magnitude, frame_width, frame_height)
        
        # Only report MEDIUM or higher
        if risk in ['none', 'low']:
            return None
        
        # Log risk
        print(f"[ani] {obj.label} → {motion} → {risk.upper()}")
        
        return {
            "label": obj.label,
            "direction": obj.direction,
            "distance": obj.distance,
            "motion": motion,
            "risk": risk,
            "track_id": obj.id
        }
    
    def _classify_motion(self, obj: TrackedObject, velocity_magnitude: float) -> str:
        """Classify object motion type."""
        # Threshold for considering object as moving (normalized coordinates)
        moving_threshold = 0.01  # pixels per second in normalized space
        
        if velocity_magnitude < moving_threshold:
            return "stationary"
        
        # Determine if approaching (moving toward center/user)
        # Y velocity > 0 means moving down/toward user in typical camera setup
        # X velocity toward center means crossing into path
        
        current_x = obj.current_position[0]
        vx, vy = obj.velocity
        
        # Check if moving toward user (vy > 0 in typical setup)
        # or moving toward center horizontally
        is_approaching = False
        is_crossing = False
        
        if abs(vy) > abs(vx):
            # Primarily vertical motion
            if vy > 0:
                is_approaching = True
        else:
            # Primarily horizontal motion
            # Moving toward center (0.5)
            if (current_x < 0.5 and vx > 0) or (current_x > 0.5 and vx < 0):
                is_crossing = True
        
        if is_approaching:
            return "approaching"
        elif is_crossing:
            return "crossing"
        else:
            return "moving"
    
    def _calculate_risk(
        self,
        obj: TrackedObject,
        velocity_magnitude: float,
        frame_width: int,
        frame_height: int
    ) -> str:
        """
        Calculate collision risk level.
        
        Returns:
            'none', 'low', 'medium', 'high', or 'imminent'
        """
        risk_score = 0.0
        
        # Factor 1: Distance (most important)
        distance_scores = {
            'very_close': 40,
            'close': 25,
            'moderate': 10,
            'far': 0
        }
        risk_score += distance_scores.get(obj.distance, 5)
        
        # Factor 2: Velocity magnitude
        # Normalize velocity (typical range 0-0.1 in normalized coords)
        velocity_normalized = min(velocity_magnitude / 0.05, 1.0)
        risk_score += velocity_normalized * 20
        
        # Factor 3: Direction alignment
        # Objects directly ahead are higher risk
        if obj.direction == 'ahead':
            risk_score += 15
        elif obj.direction in ['left', 'right']:
            risk_score += 5
        
        # Factor 4: Time to intersection (simple approximation)
        if velocity_magnitude > 0.005:  # If moving
            # Predict position
            predicted_x = obj.current_position[0] + obj.velocity[0] * self.prediction_horizon_s
            predicted_y = obj.current_position[1] + obj.velocity[1] * self.prediction_horizon_s
            
            # Check if predicted path crosses user path (center region)
            if 0.4 <= predicted_x <= 0.6 and predicted_y > obj.current_position[1]:
                risk_score += 20
        
        # Factor 5: Object type
        high_risk_labels = {'car', 'truck', 'bus', 'motorcycle', 'bicycle'}
        if obj.label.lower() in high_risk_labels:
            risk_score += 10
        
        # Map score to risk level (conservative)
        if risk_score >= 60:
            return 'imminent'
        elif risk_score >= 45:
            return 'high'
        elif risk_score >= 30:
            return 'medium'
        elif risk_score >= 15:
            return 'low'
        else:
            return 'none'
    
    def has_imminent_risk(self, assessments: List[Dict[str, Any]]) -> bool:
        """Check if any assessment has imminent risk."""
        return any(a.get('risk') == 'imminent' for a in assessments)


# Global ANI engine instance
_ani_engine: Optional[ANIEngine] = None


def initialize_ani_engine(
    max_tracking_distance: float = 0.3,
    max_missed_frames: int = 5,
    prediction_horizon_s: float = 1.5
) -> bool:
    """
    Initialize the ANI engine.
    
    Returns:
        True if successful
    """
    global _ani_engine
    try:
        _ani_engine = ANIEngine(
            max_tracking_distance=max_tracking_distance,
            max_missed_frames=max_missed_frames,
            prediction_horizon_s=prediction_horizon_s
        )
        return True
    except Exception as e:
        print(f"[ani] Failed to initialize: {e}")
        _ani_engine = None
        return False


def process_detections_with_ani(
    detections: List[Dict[str, Any]],
    frame_width: int = 1920,
    frame_height: int = 1080
) -> List[Dict[str, Any]]:
    """
    Process detections through ANI engine.
    
    Args:
        detections: List of YOLO detections
        frame_width: Frame width
        frame_height: Frame height
    
    Returns:
        List of ANI risk assessments (only MEDIUM+ risk objects)
    """
    global _ani_engine
    
    if _ani_engine is None:
        # Fallback: return empty if ANI not initialized
        return []
    
    try:
        return _ani_engine.process_frame(detections, frame_width, frame_height)
    except Exception as e:
        print(f"[ani] Processing error: {e}")
        return []


def has_imminent_risk(assessments: List[Dict[str, Any]]) -> bool:
    """Check if any assessment indicates imminent risk."""
    return any(a.get('risk') == 'imminent' for a in assessments)
