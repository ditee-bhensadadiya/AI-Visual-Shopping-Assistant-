"""Validated output from whole-image product analysis."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NormalizedBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x1: float = Field(ge=0, le=1)
    y1: float = Field(ge=0, le=1)
    x2: float = Field(ge=0, le=1)
    y2: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def ordered_coordinates(self) -> "NormalizedBox":
        if self.x2 <= self.x1 or self.y2 <= self.y1:
            raise ValueError("Product box must have positive width and height")
        return self


class AnalyzedProduct(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=100)
    brand: str | None = Field(max_length=100)
    brand_confidence: float = Field(ge=0, le=1)
    brand_evidence: Literal["visible_logo", "visible_text", "visual_style", "unknown"]
    model: str | None = Field(max_length=160)
    color: str | None = Field(max_length=100)
    confidence: float = Field(ge=0, le=1)
    box: NormalizedBox

    @model_validator(mode="after")
    def unknown_brand_has_no_confidence(self) -> "AnalyzedProduct":
        if self.brand is None and self.brand_evidence != "unknown":
            raise ValueError("Brand evidence requires a brand")
        if self.brand is None and self.brand_confidence != 0:
            raise ValueError("Unknown brands must have zero confidence")
        return self


class ProductImageAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    products: list[AnalyzedProduct] = Field(max_length=50)
