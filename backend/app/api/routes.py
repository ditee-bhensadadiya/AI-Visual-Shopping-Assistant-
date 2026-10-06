"""Phase 2 API routes."""
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(prefix="/api")


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    """Report that the HTTP service is accepting requests."""
    return HealthResponse(status="ok", service="visual-shopping-assistant-api", version="0.1.0")

