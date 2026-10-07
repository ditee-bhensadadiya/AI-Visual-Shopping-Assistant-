"""Supabase persistence for image detections."""

from typing import Any


class DetectionRepository:
    def __init__(self, client: Any) -> None:
        self._client = client

    def list_for_upload(self, upload_id: str) -> list[dict[str, Any]]:
        response = (
            self._client.table("detections")
            .select("id,crop_path")
            .eq("upload_id", upload_id)
            .execute()
        )
        return response.data or []

    def delete_for_upload(self, upload_id: str) -> None:
        self._client.table("detections").delete().eq("upload_id", upload_id).execute()

    def create_many(self, values: list[dict[str, Any]]) -> None:
        if values:
            self._client.table("detections").insert(values).execute()
