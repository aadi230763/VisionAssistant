import os
from typing import Any, Optional


class YoloDetector:
    def __init__(
        self,
        model: str | None = None,
        conf: float = 0.35,
        iou: float = 0.45,
        device: str | None = None,
    ):
        from ultralytics import YOLO

        self.model_path = model or os.getenv("YOLO_MODEL", "yolo11n.pt")
        self.conf = float(conf)
        self.iou = float(iou)
        self.device = device

        self._model = YOLO(self.model_path)

    def detect(self, frame, depth_map: Optional[Any] = None) -> list[dict[str, Any]]:
        """
        Detect objects in frame and optionally add depth information.
        
        Args:
            frame: Input frame
            depth_map: Optional depth map from depth_estimator
        
        Returns:
            List of detections with optional depth info
        """
        results = self._model.predict(
            source=frame,
            conf=self.conf,
            iou=self.iou,
            device=self.device,
            verbose=False,
        )
        if not results:
            return []

        r0 = results[0]
        if getattr(r0, "boxes", None) is None or r0.boxes is None:
            return []

        names = getattr(r0, "names", None) or getattr(self._model, "names", None) or {}
        
        # Get frame dimensions for direction calculation
        frame_height, frame_width = frame.shape[:2]

        # Keep ALL detections (don't aggregate by label to detect multiple people)
        all_detections = []
        for box in r0.boxes:
            cls = int(box.cls.item()) if hasattr(box.cls, "item") else int(box.cls)
            conf = float(box.conf.item()) if hasattr(box.conf, "item") else float(box.conf)
            label = names.get(cls, str(cls))
            
            # Get bounding box coordinates
            bbox = box.xyxy[0].cpu().numpy() if hasattr(box.xyxy[0], 'cpu') else box.xyxy[0]
            
            # Add depth information if available
            depth_info = {}
            if depth_map is not None:
                try:
                    from depth_estimator import compute_bbox_depth, get_object_direction
                    
                    median_depth, distance_bucket = compute_bbox_depth(depth_map, bbox)
                    direction = get_object_direction(bbox, frame_width)
                    
                    depth_info = {
                        "distance": distance_bucket,
                        "direction": direction,
                        "depth_value": median_depth
                    }
                    
                    # Concise depth logging with emoji indicators
                    emoji = {"very_close": "🔴", "close": "🟠", "moderate": "🟡", "far": "🟢"}.get(distance_bucket, "⚪")
                    print(f"  {emoji} {label.upper()}: {median_depth:.2f} [{distance_bucket}] → {direction}")
                except Exception as e:
                    print(f"[yolo] depth integration error: {e}")
            
            # Normalize bbox coordinates to 0-1 range for UI
            x1, y1, x2, y2 = bbox
            normalized_bbox = [
                float(x1 / frame_width),
                float(y1 / frame_height),
                float(x2 / frame_width),
                float(y2 / frame_height)
            ]
            
            # Add ALL detections to list (including multiple of same type)
            all_detections.append({
                "label": label,
                "confidence": conf,
                "bbox": normalized_bbox,
                **depth_info
            })

        # Sort by confidence (highest first)
        all_detections.sort(key=lambda d: -d["confidence"])
        return all_detections
