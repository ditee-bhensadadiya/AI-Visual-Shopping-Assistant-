"""Whole-image product detection using a local Ollama vision model."""

from __future__ import annotations

import base64
from io import BytesIO
import logging

import httpx
from PIL import Image

from app.config import Settings
from app.schemas.detections import DetectionBox, DetectionCandidate
from app.schemas.product_analysis import ProductImageAnalysis

logger = logging.getLogger("app.vision.ollama")

_INSTRUCTIONS = """Inspect the full image and identify distinct consumer products, not just a fixed list of common object classes. Include items such as clothing, shoes, bags, bottles, electronics, accessories, furniture, and other goods. Ignore people, scenery, and decorative text that is not part of a product.

For every product, return a short descriptive name and broad category. Give a brand only when supported by a visible logo, readable text, or a distinctive design you can identify with reasonable confidence. Otherwise set brand to null, brand_confidence to 0, and brand_evidence to unknown. Do not invent an exact model; use null when uncertain. Keep confidence values conservative and treat them as estimates.

Return a tight approximate bounding box around each product, as normalized coordinates from 0 to 1, with x increasing rightward and y increasing downward. Do not return a box for an object you cannot identify as a product. If there are no identifiable products, return an empty products array."""


class VisionUnavailable(RuntimeError):
    """The local vision model is unavailable or could not complete a request."""


class OllamaProductAnalyzer:
    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self.settings = settings
        self.client = client

    def analyze(self, image: Image.Image) -> list[DetectionCandidate]:
        image_data = BytesIO()
        image.convert("RGB").save(image_data, format="JPEG", quality=90, optimize=True)
        image_b64 = base64.b64encode(image_data.getvalue()).decode("ascii")
        payload = {
            "model": self.settings.ollama_vision_model,
            "stream": False,
            "format": ProductImageAnalysis.model_json_schema(),
            "options": {"temperature": 0},
            "messages": [{
                "role": "user",
                "content": _INSTRUCTIONS + "\n\nFind and describe the consumer products in this image.",
                "images": [image_b64],
            }],
        }

        try:
            if self.client is None:
                with httpx.Client(timeout=httpx.Timeout(600.0, connect=5.0)) as client:
                    response = client.post(f"{self.settings.ollama_base_url}/api/chat", json=payload)
            else:
                response = self.client.post(f"{self.settings.ollama_base_url}/api/chat", json=payload)
        except httpx.TimeoutException as exc:
            raise VisionUnavailable("Local image analysis timed out. Try a smaller image or wait and retry.") from exc
        except httpx.HTTPError as exc:
            raise VisionUnavailable(
                "Cannot connect to local Ollama. Install/start Ollama, then make sure it is listening at "
                f"{self.settings.ollama_base_url}."
            ) from exc

        if response.status_code >= 400:
            logger.warning("Ollama vision request failed", extra={"status_code": response.status_code})
            try:
                error = response.json().get("error", "")
            except (ValueError, AttributeError):
                error = ""
            if "not found" in str(error).lower():
                message = f"Ollama model '{self.settings.ollama_vision_model}' is missing. Run: ollama pull {self.settings.ollama_vision_model}"
            else:
                message = "Ollama could not analyze this image. Check that the local model is running and try again."
            raise VisionUnavailable(message)

        try:
            data = response.json()
            output = data["message"]["content"]
            analysis = ProductImageAnalysis.model_validate_json(output)
        except (ValueError, KeyError, TypeError) as exc:
            logger.exception("Ollama vision returned an invalid product analysis")
            raise VisionUnavailable("Local vision model returned an invalid result. Please try again.") from exc

        width, height = image.size
        return [
            DetectionCandidate(
                class_name=product.name,
                confidence=product.confidence,
                box=DetectionBox(
                    x1=product.box.x1 * width,
                    y1=product.box.y1 * height,
                    x2=product.box.x2 * width,
                    y2=product.box.y2 * height,
                ),
                category=product.category,
                brand=product.brand,
                brand_confidence=product.brand_confidence,
                brand_evidence=product.brand_evidence,
                model=product.model,
                color=product.color,
            )
            for product in analysis.products
        ]
