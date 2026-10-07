"""Validated product-detection output."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DetectionBox(BaseModel):
    model_config = ConfigDict(frozen=True)

    x1: float = Field(ge=0)
    y1: float = Field(ge=0)
    x2: float = Field(ge=0)
    y2: float = Field(ge=0)

    @model_validator(mode="after")
    def ordered_coordinates(self) -> "DetectionBox":
        if self.x2 <= self.x1 or self.y2 <= self.y1:
            raise ValueError("Bounding box must have positive width and height")
        return self


class DetectionCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    class_name: str = Field(min_length=1, max_length=100)
    confidence: float = Field(ge=0, le=1)
    box: DetectionBox
    category: str | None = Field(default=None, max_length=100)
    brand: str | None = Field(default=None, max_length=100)
    brand_confidence: float | None = Field(default=None, ge=0, le=1)
    brand_evidence: str | None = Field(default=None, max_length=30)
    model: str | None = Field(default=None, max_length=160)
    color: str | None = Field(default=None, max_length=100)


class DetectionResult(DetectionCandidate):
    id: str
    crop_url: str


class DetectionRunResponse(BaseModel):
    upload_id: str
    processing_status: str
    image_width: int = Field(gt=0)
    image_height: int = Field(gt=0)
    analysis_provider: str = "ollama"
    analysis_model: str
    detections: list[DetectionResult]
