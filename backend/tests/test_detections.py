"""Tests for the detector adapter and persisted detection endpoint."""

from io import BytesIO
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from uuid import UUID

import httpx
from PIL import Image

from app.config import Settings
from app.main import create_app
from app.schemas.detections import DetectionBox, DetectionCandidate
from app.services.detectors.yolo import YOLODetector
from app.services.vision.ollama import VisionUnavailable


class _Tensor:
    def __init__(self, values):
        self.values = values

    def cpu(self):
        return self

    def tolist(self):
        return self.values


class _FakeModel:
    def __init__(self, results):
        self.results = results
        self.kwargs = None

    def predict(self, **kwargs):
        self.kwargs = kwargs
        return self.results


class _FakeTable:
    def __init__(self, client, name):
        self.client = client
        self.name = name
        self.operation = None
        self.values = None
        self.filters = []

    def select(self, _columns):
        self.operation = "select"
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def maybe_single(self):
        return self

    def update(self, values):
        self.operation, self.values = "update", values
        return self

    def insert(self, values):
        self.operation, self.values = "insert", values
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def execute(self):
        identifier = next((value for key, value in self.filters if key in {"id", "upload_id"}), None)
        if self.name == "uploads":
            if self.operation == "select":
                row = self.client.upload if identifier == self.client.upload["id"] else None
                return SimpleNamespace(data=row)
            if self.operation == "update" and identifier == self.client.upload["id"]:
                status_filter = next((value for key, value in self.filters if key == "processing_status"), None)
                if status_filter and self.client.upload["processing_status"] != status_filter:
                    return SimpleNamespace(data=[])
                self.client.upload.update(self.values)
                return SimpleNamespace(data=[self.client.upload])
        elif self.name == "detections":
            if self.operation == "select":
                rows = [row for row in self.client.detections if row["upload_id"] == identifier]
                return SimpleNamespace(data=rows)
            if self.operation == "insert":
                self.client.detections.extend(self.values)
                return SimpleNamespace(data=self.values)
            if self.operation == "delete":
                self.client.detections = [row for row in self.client.detections if row["upload_id"] != identifier]
        return SimpleNamespace(data=[])


class _FakeStorage:
    def __init__(self, original):
        self.objects = {"anonymous/original.png": original}

    def from_(self, _bucket):
        return self

    def download(self, path):
        return self.objects[path]

    def upload(self, path, content, file_options=None):
        self.objects[path] = content

    def remove(self, paths):
        for path in paths:
            self.objects.pop(path, None)

    def create_signed_url(self, path, _expires_in):
        return {"signedURL": f"https://storage.example.test/{path}?token=test"}


class _FakeClient:
    def __init__(self, original):
        self.upload = {
            "id": "11111111-1111-4111-8111-111111111111",
            "file_path": "anonymous/original.png",
            "processing_status": "uploaded",
        }
        self.detections = []
        self.storage = _FakeStorage(original)

    def table(self, name):
        return _FakeTable(self, name)


class DetectorAdapterTests(unittest.TestCase):
    def test_converts_yolo_output_to_pixel_box_candidates(self):
        boxes = SimpleNamespace(
            xyxy=_Tensor([[4.0, 5.0, 20.0, 25.0]]),
            conf=_Tensor([0.91]),
            cls=_Tensor([26]),
        )
        model = _FakeModel([SimpleNamespace(boxes=boxes, names={26: "handbag"})])
        settings = Settings(cors_origins=(), log_level=50)
        detector = YOLODetector(settings, model=model)
        image = Image.new("RGB", (32, 32), "white")

        detections = detector.detect(image)

        self.assertEqual(detections, [DetectionCandidate(
            class_name="handbag",
            confidence=0.91,
            box=DetectionBox(x1=4, y1=5, x2=20, y2=25),
        )])
        self.assertEqual(model.kwargs["conf"], 0.25)
        self.assertEqual(model.kwargs["source"], image)


class DetectionEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        image_bytes = BytesIO()
        Image.new("RGB", (40, 30), "green").save(image_bytes, format="PNG")
        self.client_db = _FakeClient(image_bytes.getvalue())
        self.app = create_app(Settings(cors_origins=(), log_level=50))
        self.http = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app),
            base_url="http://testserver",
        )

    async def asyncTearDown(self):
        await self.http.aclose()

    async def test_detection_persists_boxes_and_crop_and_completes_upload(self):
        analyzer = SimpleNamespace(analyze=lambda _image: [DetectionCandidate(
            class_name="handbag",
            confidence=0.91,
            box=DetectionBox(x1=4, y1=5, x2=20, y2=25),
            category="bag",
            brand="Northwind",
            brand_confidence=0.83,
            brand_evidence="visible_logo",
        )])
        with patch("app.api.detections.get_supabase_client", return_value=self.client_db), patch(
            "app.api.detections.OllamaProductAnalyzer", return_value=analyzer
        ):
            response = await self.http.post(
                "/api/uploads/11111111-1111-4111-8111-111111111111/detect"
            )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["processing_status"], "completed")
        self.assertEqual((body["image_width"], body["image_height"]), (40, 30))
        self.assertEqual(body["detections"][0]["class_name"], "handbag")
        self.assertEqual(body["detections"][0]["brand"], "Northwind")
        self.assertEqual(body["detections"][0]["category"], "bag")
        self.assertEqual(body["detections"][0]["box"], {"x1": 4, "y1": 5, "x2": 20, "y2": 25})
        self.assertTrue(body["detections"][0]["crop_url"].startswith("https://storage.example.test/crops/"))
        self.assertEqual(self.client_db.upload["processing_status"], "completed")
        self.assertEqual(len(self.client_db.detections), 1)
        self.assertEqual(len(self.client_db.storage.objects), 2)

    async def test_unknown_upload_returns_404(self):
        self.client_db.upload["id"] = "22222222-2222-4222-8222-222222222222"
        with patch("app.api.detections.get_supabase_client", return_value=self.client_db):
            response = await self.http.post(
                "/api/uploads/11111111-1111-4111-8111-111111111111/detect"
            )
        self.assertEqual(response.status_code, 404)

    async def test_unavailable_vision_marks_upload_failed(self):
        with patch("app.api.detections.get_supabase_client", return_value=self.client_db), patch(
            "app.api.detections.OllamaProductAnalyzer",
            side_effect=VisionUnavailable("Local Ollama is unavailable"),
        ):
            response = await self.http.post(
                "/api/uploads/11111111-1111-4111-8111-111111111111/detect"
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.client_db.upload["processing_status"], "failed")


if __name__ == "__main__":
    unittest.main()
