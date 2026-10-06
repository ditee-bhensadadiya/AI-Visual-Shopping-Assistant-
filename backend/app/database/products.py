"""CRUD repository for catalog products."""

from __future__ import annotations

from typing import Any
from uuid import UUID


class ProductRepository:
    """Small persistence boundary around Supabase's PostgREST API."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def create(self, values: dict[str, Any]) -> dict[str, Any]:
        response = self._client.table("products").insert(values).execute()
        return self._one(response.data, "create")

    def get(self, product_id: UUID) -> dict[str, Any] | None:
        response = (
            self._client.table("products")
            .select("*")
            .eq("id", str(product_id))
            .maybe_single()
            .execute()
        )
        return response.data

    def update(self, product_id: UUID, values: dict[str, Any]) -> dict[str, Any]:
        if not values:
            raise ValueError("At least one product field is required")
        response = (
            self._client.table("products")
            .update(values)
            .eq("id", str(product_id))
            .execute()
        )
        return self._one(response.data, "update")

    def delete(self, product_id: UUID) -> None:
        self._client.table("products").delete().eq("id", str(product_id)).execute()

    @staticmethod
    def _one(rows: list[dict[str, Any]] | None, operation: str) -> dict[str, Any]:
        if not rows:
            raise LookupError(f"Product {operation} returned no row")
        return rows[0]
