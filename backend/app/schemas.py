from datetime import datetime

from pydantic import BaseModel, Field

from app.registry import AspectPreset, Style


class ModelInfo(BaseModel):
    id: str
    display_name: str
    provider: str
    supports_negative_prompt: bool
    supports_seed: bool
    estimated_credits: int


class GenerationCreateRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=4000)
    style: Style
    aspect_preset: AspectPreset
    purpose: str | None = None
    negative_prompt: str | None = None
    seed: int | None = None
    model_ids: list[str] = Field(min_length=1, max_length=10)


class GenerationTaskOut(BaseModel):
    id: str
    model_id: str
    status: str
    image_url: str | None = None
    cost_credits: float | None = None
    duration_ms: int | None = None
    error: str | None = None

    class Config:
        from_attributes = True


class GenerationBatchOut(BaseModel):
    id: str
    prompt: str
    style: str
    aspect_preset: str
    purpose: str | None = None
    status: str
    total_cost_credits: float
    created_at: datetime
    tasks: list[GenerationTaskOut] = []

    class Config:
        from_attributes = True


class GenerationBatchSummary(BaseModel):
    id: str
    prompt: str
    style: str
    aspect_preset: str
    purpose: str | None = None
    status: str
    total_cost_credits: float
    created_at: datetime
    model_ids: list[str] = []

    class Config:
        from_attributes = True


class CreditInfo(BaseModel):
    raw: dict
