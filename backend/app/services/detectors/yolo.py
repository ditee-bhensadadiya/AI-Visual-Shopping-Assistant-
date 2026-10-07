"""Lazy, local Ultralytics YOLO detector adapter."""

from functools import lru_cache
import logging
from threading import Lock

from PIL import Image

from app.config import Settings
from app.schemas.detections import DetectionBox, DetectionCandidate

logger = logging.getLogger("app.detection")


class DetectorUnavailable(RuntimeError):
    """The configured model or its runtime could not be loaded."""


class YOLODetector:
    """Run a pretrained Ultralytics object detector on one in-memory image."""

    def __init__(self, settings: Settings, model=None) -> None:
        self._settings = settings
        self._lock = Lock()
        if model is not None:
            self._model = model
            return
        try:
            from ultralytics import YOLO

            self._model = YOLO(settings.yolo_model_path)
        except Exception as exc:
            logger.exception("YOLO model could not be loaded")
            raise DetectorUnavailable(
                "YOLO is unavailable. Install backend requirements and check YOLO_MODEL_PATH."
            ) from exc

    def detect(self, image: Image.Image) -> list[DetectionCandidate]:
        try:
            with self._lock:
                results = self._model.predict(
                    source=image,
                    conf=self._settings.yolo_confidence_threshold,
                    iou=self._settings.yolo_iou_threshold,
                    max_det=self._settings.yolo_max_detections,
                    imgsz=640,
                    verbose=False,
                )
        except Exception as exc:
            logger.exception("YOLO inference failed")
            raise RuntimeError("YOLO inference failed") from exc

        detections: list[DetectionCandidate] = []
        for result in results or []:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            coordinates = boxes.xyxy.cpu().tolist()
            confidences = boxes.conf.cpu().tolist()
            class_ids = boxes.cls.cpu().tolist()
            names = result.names
            for xyxy, confidence, class_id in zip(coordinates, confidences, class_ids):
                class_name = names.get(int(class_id), str(int(class_id))) if isinstance(names, dict) else names[int(class_id)]
                x1, y1, x2, y2 = (float(value) for value in xyxy)
                detections.append(DetectionCandidate(
                    class_name=str(class_name),
                    confidence=float(confidence),
                    box=DetectionBox(x1=x1, y1=y1, x2=x2, y2=y2),
                ))
        return detections


@lru_cache(maxsize=4)
def get_detector(settings: Settings) -> YOLODetector:
    """Cache model weights per configuration, loading them only on first use."""
    return YOLODetector(settings)
