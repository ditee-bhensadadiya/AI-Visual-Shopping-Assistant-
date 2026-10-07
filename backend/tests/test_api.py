"""Tests for Phase 2 API, CORS, request IDs, and error contracts."""
import os
import unittest
from io import BytesIO
from unittest.mock import Mock, patch

import httpx
from PIL import Image

from app.config import Settings
from app.main import create_app


class ApiFoundationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        app = create_app(Settings(
            cors_origins=("http://localhost:5173",),
            log_level=50,
            max_upload_bytes=1024 * 1024,
        ))
        transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(transport=transport, base_url="http://testserver")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_health_response_and_request_id(self):
        response = await self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "status": "ok",
            "service": "visual-shopping-assistant-api",
            "version": "0.1.0",
        })
        self.assertTrue(response.headers.get("x-request-id"))

    async def test_cors_allows_frontend_origin(self):
        response = await self.client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "http://localhost:5173",
        )

    async def test_upload_stores_image_and_returns_signed_preview(self):
        image_bytes = BytesIO()
        Image.new("RGB", (2, 2), "green").save(image_bytes, format="PNG")
        storage = Mock()
        storage.create_signed_url.return_value = {"signedURL": "/object/sign/uploads/test.png?token=abc"}
        table = Mock()
        table.insert.return_value.execute.return_value.data = [{
            "file_type": "image/png",
            "file_size": len(image_bytes.getvalue()),
            "created_at": "2026-10-07T00:00:00+00:00",
        }]
        client = Mock()
        client.storage.from_.return_value = storage
        client.table.return_value = table
        with patch("app.api.uploads.get_supabase_client", return_value=client), patch(
            "app.api.uploads._absolute_signed_url",
            return_value="https://example.supabase.co/storage/v1/object/sign/uploads/test.png?token=abc",
        ):
            response = await self.client.post(
                "/api/uploads",
                files={"file": ("sample.png", image_bytes.getvalue(), "image/png")},
            )
        self.assertEqual(response.status_code, 201, response.text)
        data = response.json()
        self.assertEqual(data["processing_status"], "uploaded")
        self.assertTrue(data["image_url"].startswith("https://example.supabase.co/"))
        inserted = table.insert.call_args.args[0]
        self.assertIsNone(inserted["user_id"])
        self.assertTrue(inserted["file_path"].startswith("anonymous/"))
        storage.upload.assert_called_once()

    async def test_upload_rejects_invalid_image_content(self):
        response = await self.client.post(
            "/api/uploads",
            files={"file": ("sample.png", b"not an image", "image/png")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    async def test_http_errors_have_consistent_shape(self):
        response = await self.client.get("/missing")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "http_error")
        self.assertTrue(response.json()["request_id"])

    def test_settings_parse_origins_and_reject_bad_log_level(self):
        with patch.dict(os.environ, {
            "BACKEND_CORS_ORIGINS": "http://localhost:5173, https://example.test/",
            "LOG_LEVEL": "WARNING",
        }, clear=True):
            settings = Settings.from_env()
        self.assertEqual(
            settings.cors_origins,
            ("http://localhost:5173", "https://example.test"),
        )
        self.assertEqual(settings.log_level, 30)
        with patch.dict(os.environ, {"LOG_LEVEL": "NOPE"}, clear=True):
            with self.assertRaisesRegex(ValueError, "LOG_LEVEL"):
                Settings.from_env()


if __name__ == "__main__":
    unittest.main()
