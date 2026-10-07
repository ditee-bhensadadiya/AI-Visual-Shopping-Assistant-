"""Image upload endpoint for Phase 3."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
import logging
from typing import Literal
from urllib.parse import urljoin
from uuid import UUID, uuid4

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel

from app.database.client import SupabaseSettings, get_supabase_client

router = APIRouter(prefix="/api", tags=["uploads"])
logger = logging.getLogger("app.uploads")

ALLOWED_FORMATS = {
    "image/jpeg": ("JPEG", ".jpg"),
    "image/png": ("PNG", ".png"),
    "image/webp": ("WEBP", ".webp"),
}
MAX_IMAGE_PIXELS = 40_000_000
SIGNED_URL_TTL_SECONDS = 3600


class UploadResponse(BaseModel):
    id: UUID
    file_type: str
    file_size: int
    processing_status: Literal["uploaded"]
    image_url: str
    created_at: datetime


def _validate_image(content: bytes, content_type: str, max_bytes: int) -> tuple[str, str]:
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="Image exceeds the configured upload size limit")
    expected = ALLOWED_FORMATS.get(content_type.lower().split(";")[0].strip())
    if expected is None:
        raise HTTPException(status_code=415, detail="Choose a JPEG, PNG, or WebP image")
    try:
        with Image.open(BytesIO(content)) as image:
            image_format = image.format
            width, height = image.size
            image.verify()
        if image_format != expected[0]:
            raise HTTPException(status_code=415, detail="File contents do not match the selected image type")
        if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
            raise HTTPException(status_code=400, detail="Image dimensions are invalid or too large")
        with Image.open(BytesIO(content)) as image:
            image.load()
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError) as exc:
        raise HTTPException(status_code=400, detail="The image is corrupt or could not be decoded") from exc
    return expected


def _absolute_signed_url(signed_url: str) -> str:
    if signed_url.startswith(("https://", "http://")):
        return signed_url
    base_url = SupabaseSettings.from_env().url
    storage_path = signed_url if signed_url.startswith("/storage/v1/") else f"/storage/v1{signed_url}"
    return urljoin(base_url + "/", storage_path.lstrip("/"))


@router.post("/uploads", response_model=UploadResponse, status_code=201)
def upload_image(request: Request, file: UploadFile = File(...)) -> UploadResponse:
    """Validate and privately store one image, then record its upload state."""
    settings = request.app.state.settings
    content_type = (file.content_type or "").lower()
    # Read at most one byte beyond the configured limit, even for chunked requests.
    content = file.file.read(settings.max_upload_bytes + 1)
    _, extension = _validate_image(content, content_type, settings.max_upload_bytes)

    upload_id = uuid4()
    file_path = f"anonymous/{upload_id}{extension}"
    client = get_supabase_client()
    stored = False
    try:
        client.storage.from_("uploads").upload(
            file_path,
            content,
            file_options={"content-type": content_type, "upsert": "false"},
        )
        stored = True
        response = client.table("uploads").insert({
            "id": str(upload_id),
            "user_id": None,
            "file_path": file_path,
            "file_type": content_type,
            "file_size": len(content),
            "processing_status": "uploaded",
        }).execute()
        if not response.data:
            raise RuntimeError("Upload record insert returned no row")
        row = response.data[0]
        signed = client.storage.from_("uploads").create_signed_url(
            file_path, SIGNED_URL_TTL_SECONDS
        )
        signed_url = signed.get("signedURL") or signed.get("signedUrl")
        if not signed_url:
            raise RuntimeError("Storage did not return a preview URL")
        return UploadResponse(
            id=upload_id,
            file_type=row.get("file_type", content_type),
            file_size=row.get("file_size", len(content)),
            processing_status="uploaded",
            image_url=_absolute_signed_url(signed_url),
            created_at=row.get("created_at", datetime.now().astimezone()),
        )
    except HTTPException:
        raise
    except Exception as exc:
        if stored:
            try:
                client.storage.from_("uploads").remove([file_path])
                client.table("uploads").delete().eq("id", str(upload_id)).execute()
            except Exception:
                logger.warning("upload cleanup failed", extra={"upload_id": str(upload_id)})
        logger.exception("image upload failed", extra={"upload_id": str(upload_id)})
        raise HTTPException(status_code=502, detail="Image could not be saved. Please try again.") from exc
