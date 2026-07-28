from fastapi import APIRouter

from app.registry import list_active_models
from app.schemas import ModelInfo

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=list[ModelInfo])
def get_models():
    return [
        ModelInfo(
            id=m.id,
            display_name=m.display_name,
            provider=m.provider,
            supports_negative_prompt=m.supports_negative_prompt,
            supports_seed=m.supports_seed,
            estimated_credits=m.estimated_credits,
        )
        for m in list_active_models()
    ]
