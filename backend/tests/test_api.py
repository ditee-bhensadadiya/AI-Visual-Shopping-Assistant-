"""Tests for Phase 2 API, CORS, request IDs, and error contracts."""
import os
import unittest
from unittest.mock import patch

import httpx

from app.config import Settings
from app.main import create_app


class ApiFoundationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        app = create_app(Settings(
            cors_origins=("http://localhost:5173",),
            log_level=50,
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
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "http://localhost:5173",
        )

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
