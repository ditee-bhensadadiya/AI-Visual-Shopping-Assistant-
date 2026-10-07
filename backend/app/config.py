"""Environment-backed settings for the API."""
from dataclasses import dataclass
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    cors_origins: tuple[str, ...]
    log_level: int
    max_upload_bytes: int = 10 * 1024 * 1024
    yolo_model_path: str = "yolo26n.pt"
    yolo_confidence_threshold: float = 0.25
    yolo_iou_threshold: float = 0.7
    yolo_max_detections: int = 50
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_vision_model: str = "qwen3-vl:4b-instruct"

    @classmethod
    def from_env(cls) -> "Settings":
        raw_origins = os.getenv(
            "BACKEND_CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        )
        origins = tuple(origin.strip().rstrip("/") for origin in raw_origins.split(",") if origin.strip())
        raw_level = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, raw_level, None)
        if not isinstance(level, int):
            raise ValueError("LOG_LEVEL must be a valid Python logging level")
        try:
            max_upload_bytes = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
        except ValueError as exc:
            raise ValueError("MAX_UPLOAD_BYTES must be an integer") from exc
        if max_upload_bytes <= 0:
            raise ValueError("MAX_UPLOAD_BYTES must be positive")
        try:
            confidence = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.25"))
            iou = float(os.getenv("YOLO_IOU_THRESHOLD", "0.7"))
            max_detections = int(os.getenv("YOLO_MAX_DETECTIONS", "50"))
        except ValueError as exc:
            raise ValueError("YOLO confidence, IoU, and detection limit settings are invalid") from exc
        if not 0 < confidence <= 1:
            raise ValueError("YOLO_CONFIDENCE_THRESHOLD must be greater than 0 and at most 1")
        if not 0 < iou <= 1:
            raise ValueError("YOLO_IOU_THRESHOLD must be greater than 0 and at most 1")
        if max_detections <= 0:
            raise ValueError("YOLO_MAX_DETECTIONS must be positive")
        return cls(
            cors_origins=origins,
            log_level=level,
            max_upload_bytes=max_upload_bytes,
            yolo_model_path=os.getenv("YOLO_MODEL_PATH", "yolo26n.pt").strip() or "yolo26n.pt",
            yolo_confidence_threshold=confidence,
            yolo_iou_threshold=iou,
            yolo_max_detections=max_detections,
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/"),
            ollama_vision_model=os.getenv("OLLAMA_VISION_MODEL", "qwen3-vl:4b-instruct").strip() or "qwen3-vl:4b-instruct",
        )

