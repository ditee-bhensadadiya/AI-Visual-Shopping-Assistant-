"""Unit tests for Supabase configuration and product CRUD adapter."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch
from uuid import UUID

from app.database.client import SupabaseSettings
from app.database.products import ProductRepository


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, client):
        self.client = client
        self.operation = None
        self.values = None
        self.filters = []

    def insert(self, values):
        self.operation, self.values = "insert", values
        return self

    def select(self, _columns):
        self.operation = "select"
        return self

    def update(self, values):
        self.operation, self.values = "update", values
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def maybe_single(self):
        return self

    def execute(self):
        self.client.calls.append((self.operation, self.values, self.filters))
        if self.operation == "delete":
            return _Response([])
        if self.operation == "select":
            row = self.client.rows.get(self.filters[0][1])
            return _Response(row)
        if self.operation == "insert":
            row = {"id": str(self.client.next_id), **self.values}
            self.client.rows[row["id"]] = row
            return _Response([row])
        if self.operation == "update":
            product_id = self.filters[0][1]
            self.client.rows[product_id].update(self.values)
            return _Response([self.client.rows[product_id]])


class _FakeSupabase:
    def __init__(self):
        self.rows = {}
        self.calls = []
        self.next_id = UUID("00000000-0000-0000-0000-000000000001")

    def table(self, name):
        if name != "products":
            raise AssertionError(f"Unexpected table: {name}")
        return _Query(self)


class SupabaseSettingsTests(unittest.TestCase):
    def test_reads_server_side_credentials(self):
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://example.supabase.co/",
            "SUPABASE_SERVICE_ROLE_KEY": "server-secret",
        }, clear=True):
            self.assertEqual(
                SupabaseSettings.from_env(),
                SupabaseSettings("https://example.supabase.co", "server-secret"),
            )

    def test_missing_credentials_fail_clearly(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "SUPABASE_URL"):
                SupabaseSettings.from_env()

    def test_invalid_url_is_rejected(self):
        with patch.dict(os.environ, {
            "SUPABASE_URL": "not-a-url",
            "SUPABASE_SERVICE_ROLE_KEY": "server-secret",
        }, clear=True):
            with self.assertRaisesRegex(ValueError, "absolute HTTP"):
                SupabaseSettings.from_env()


class ProductRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.client = _FakeSupabase()
        self.repository = ProductRepository(self.client)
        self.product_id = UUID("00000000-0000-0000-0000-000000000001")

    def test_crud(self):
        created = self.repository.create({"name": "Canvas Backpack"})
        self.assertEqual(created["name"], "Canvas Backpack")
        self.assertEqual(self.repository.get(self.product_id), created)
        updated = self.repository.update(self.product_id, {"brand": "Northwind"})
        self.assertEqual(updated["brand"], "Northwind")
        self.repository.delete(self.product_id)
        self.assertEqual(
            [call[0] for call in self.client.calls],
            ["insert", "select", "update", "delete"],
        )

    def test_update_requires_fields(self):
        with self.assertRaisesRegex(ValueError, "(?i)at least one"):
            self.repository.update(self.product_id, {})


if __name__ == "__main__":
    unittest.main()
