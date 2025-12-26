import os
from typing import Any


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

    def detect(self, frame) -> list[dict[str, Any]]:
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

        aggregated: dict[str, float] = {}
        for box in r0.boxes:
            cls = int(box.cls.item()) if hasattr(box.cls, "item") else int(box.cls)
            conf = float(box.conf.item()) if hasattr(box.conf, "item") else float(box.conf)
            label = names.get(cls, str(cls))
            prev = aggregated.get(label)
            if prev is None or conf > prev:
                aggregated[label] = conf

        detections = [{"label": label, "confidence": conf} for label, conf in aggregated.items()]
        detections.sort(key=lambda d: (-d["confidence"], d["label"]))
        return detections
