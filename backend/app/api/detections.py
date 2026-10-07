"""Run YOLO on a stored upload, persist detections, and provide crop previews."""

from __future__ import annotations

from io import BytesIO
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request
from PIL import Image, UnidentifiedImageError

from app.database.client import get_supabase_client
from app.database.detections import DetectionRepository
from app.schemas.detections import DetectionBox, DetectionCandidate, DetectionResult, DetectionRunResponse
from app.services.vision.ollama import OllamaProductAnalyzer, VisionUnavailable

router = APIRouter(prefix="/api", tags=["detections"])
logger = logging.getLogger("app.detection")
BUCKET = "uploads"


def _crop_bytes(image: Image.Image, box: DetectionBox) -> bytes:
    left = max(0, min(image.width - 1, int(box.x1)))
    top = max(0, min(image.height - 1, int(box.y1)))
    right = max(left + 1, min(image.width, int(box.x2 + 0.999)))
    bottom = max(top + 1, min(image.height, int(box.y2 + 0.999)))
    output = BytesIO()
    image.crop((left, top, right, bottom)).save(output, format="JPEG", quality=90, optimize=True)
    return output.getvalue()


def _clean_existing(client, repository: DetectionRepository, upload_id: str) -> None:
    previous = repository.list_for_upload(upload_id)
    paths = [row["crop_path"] for row in previous if row.get("crop_path")]
    if paths:
        client.storage.from_(BUCKET).remove(paths)
    if previous:
        repository.delete_for_upload(upload_id)


@router.post("/uploads/{upload_id}/detect", response_model=DetectionRunResponse)
def detect_upload(upload_id: UUID, request: Request) -> DetectionRunResponse:
    settings = request.app.state.settings
    client = get_supabase_client()
    identifier = str(upload_id)
    response = (
        client.table("uploads")
        .select("id,file_path,processing_status")
        .eq("id", identifier)
        .maybe_single()
        .execute()
    )
    upload = response.data
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload["processing_status"] == "processing":
        raise HTTPException(status_code=409, detail="This upload is already being processed")
    repository = DetectionRepository(client)
    storage = client.storage.from_(BUCKET)
    claim = (
        client.table("uploads")
        .update({"processing_status": "processing"})
        .eq("id", identifier)
        .eq("processing_status", upload["processing_status"])
        .execute()
    )
    if not claim.data:
        raise HTTPException(status_code=409, detail="This upload has already been claimed for processing")
    crop_paths: list[str] = []
    rows: list[dict] = []
    saved_candidates: list[DetectionCandidate] = []
    try:
        _clean_existing(client, repository, identifier)
        content = storage.download(upload["file_path"])
        try:
            with Image.open(BytesIO(content)) as source:
                source.load()
                image = source.convert("RGB")
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="The stored upload is not a readable image") from exc

        try:
            candidates = OllamaProductAnalyzer(settings).analyze(image)
        except VisionUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        image_width, image_height = image.size
        results: list[DetectionResult] = []
        for candidate in candidates:
            # Revalidate provider output and clamp boxes to the source image.
            candidate = DetectionCandidate.model_validate(candidate)
            box = DetectionBox(
                x1=max(0, min(float(image_width - 1), candidate.box.x1)),
                y1=max(0, min(float(image_height - 1), candidate.box.y1)),
                x2=max(0, min(float(image_width), candidate.box.x2)),
                y2=max(0, min(float(image_height), candidate.box.y2)),
            )
            if box.x2 <= box.x1 or box.y2 <= box.y1:
                continue
            detection_id = uuid4()
            crop_path = f"crops/{identifier}/{detection_id}.jpg"
            storage.upload(
                crop_path,
                _crop_bytes(image, box),
                file_options={"content-type": "image/jpeg", "upsert": "false"},
            )
            crop_paths.append(crop_path)
            saved_candidates.append(candidate)
            rows.append({
                "id": str(detection_id),
                "upload_id": identifier,
                "class_name": candidate.class_name,
                "confidence": candidate.confidence,
                "x1": box.x1,
                "y1": box.y1,
                "x2": box.x2,
                "y2": box.y2,
                "crop_path": crop_path,
            })

        repository.create_many(rows)
        if rows:
            client.table("identified_products").insert([
                {
                    "detection_id": row["id"],
                    "brand": candidate.brand,
                    "category": candidate.category,
                    "model": candidate.model,
                    "color": candidate.color,
                    "description": candidate.class_name,
                    "confidence": candidate.confidence,
                }
                for row, candidate in zip(rows, saved_candidates, strict=True)
            ]).execute()
        for row, candidate in zip(rows, saved_candidates, strict=True):
            signed = storage.create_signed_url(row["crop_path"], 3600)
            crop_url = signed.get("signedURL") or signed.get("signedUrl")
            if not crop_url:
                raise RuntimeError("Storage did not return a crop preview URL")
            results.append(DetectionResult(
                id=row["id"],
                class_name=row["class_name"],
                confidence=row["confidence"],
                category=candidate.category,
                brand=candidate.brand,
                brand_confidence=candidate.brand_confidence,
                brand_evidence=candidate.brand_evidence,
                model=candidate.model,
                color=candidate.color,
                box=DetectionBox(x1=row["x1"], y1=row["y1"], x2=row["x2"], y2=row["y2"]),
                crop_url=crop_url,
            ))

        client.table("uploads").update({"processing_status": "completed"}).eq("id", identifier).execute()
        return DetectionRunResponse(
            upload_id=identifier,
            processing_status="completed",
            image_width=image_width,
            image_height=image_height,
            analysis_provider="ollama",
            analysis_model=settings.ollama_vision_model,
            detections=results,
        )
    except HTTPException as exc:
        _fail_run(client, repository, identifier, crop_paths, exc)
        raise
    except Exception as exc:
        _fail_run(client, repository, identifier, crop_paths, exc)
        logger.exception("detection run failed", extra={"upload_id": identifier})
        raise HTTPException(status_code=502, detail="Image detection failed. Please try again.") from exc


def _fail_run(client, repository: DetectionRepository, upload_id: str, crop_paths: list[str], error: Exception) -> None:
    if crop_paths:
        try:
            client.storage.from_(BUCKET).remove(crop_paths)
        except Exception:
            logger.warning("detection crop cleanup failed", extra={"upload_id": upload_id})
    try:
        repository.delete_for_upload(upload_id)
        client.table("uploads").update({"processing_status": "failed"}).eq("id", upload_id).execute()
    except Exception:
        logger.warning("detection failure status could not be saved", extra={"upload_id": upload_id})
