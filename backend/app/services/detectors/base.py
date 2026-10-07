"""Detector interface shared by API orchestration and model adapters."""

from typing import Protocol

from PIL import Image

from app.schemas.detections import DetectionCandidate


class Detector(Protocol):
    def detect(self, image: Image.Image) -> list[DetectionCandidate]:
        """Return validated object boxes in source-image pixel coordinates."""
