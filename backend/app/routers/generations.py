from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import GenerationBatch, GenerationTask
from app.registry import get_model
from app.schemas import (
    GenerationBatchOut,
    GenerationBatchSummary,
    GenerationCreateRequest,
    GenerationTaskOut,
)
from app.services.generation_service import create_batch, start_batch_processing
from app.storage import get_storage

router = APIRouter(prefix="/generations", tags=["generations"])


def _task_out(task: GenerationTask) -> GenerationTaskOut:
    image_url = f"/generations/{task.batch_id}/tasks/{task.id}/download" if task.image_path else None
    return GenerationTaskOut(
        id=task.id,
        model_id=task.model_id,
        status=task.status,
        image_url=image_url,
        cost_credits=task.cost_credits,
        duration_ms=task.duration_ms,
        error=task.error,
    )


@router.post("", response_model=GenerationBatchOut)
async def create_generation(req: GenerationCreateRequest, db: Session = Depends(get_db)):
    unknown = [mid for mid in req.model_ids if get_model(mid) is None]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Неизвестные модели: {unknown}")

    batch = create_batch(db, req)
    start_batch_processing(batch.id)

    return GenerationBatchOut(
        id=batch.id,
        prompt=batch.prompt,
        style=batch.style,
        aspect_preset=batch.aspect_preset,
        purpose=batch.purpose,
        status=batch.status,
        total_cost_credits=batch.total_cost_credits,
        created_at=batch.created_at,
        tasks=[_task_out(t) for t in batch.tasks],
    )


@router.get("", response_model=list[GenerationBatchSummary])
def list_generations(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    style: str | None = None,
    model_id: str | None = None,
):
    query = db.query(GenerationBatch)
    if style:
        query = query.filter(GenerationBatch.style == style)
    if model_id:
        query = query.join(GenerationTask).filter(GenerationTask.model_id == model_id)

    batches = (
        query.order_by(desc(GenerationBatch.created_at)).offset(offset).limit(limit).all()
    )
    return [
        GenerationBatchSummary(
            id=b.id,
            prompt=b.prompt,
            style=b.style,
            aspect_preset=b.aspect_preset,
            purpose=b.purpose,
            status=b.status,
            total_cost_credits=b.total_cost_credits,
            created_at=b.created_at,
            model_ids=[t.model_id for t in b.tasks],
        )
        for b in batches
    ]


@router.get("/{batch_id}", response_model=GenerationBatchOut)
def get_generation(batch_id: str, db: Session = Depends(get_db)):
    batch = db.get(GenerationBatch, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Батч не найден")
    return GenerationBatchOut(
        id=batch.id,
        prompt=batch.prompt,
        style=batch.style,
        aspect_preset=batch.aspect_preset,
        purpose=batch.purpose,
        status=batch.status,
        total_cost_credits=batch.total_cost_credits,
        created_at=batch.created_at,
        tasks=[_task_out(t) for t in batch.tasks],
    )


@router.get("/{batch_id}/tasks/{task_id}/download")
def download_task_image(batch_id: str, task_id: str, db: Session = Depends(get_db)):
    task = db.get(GenerationTask, task_id)
    if task is None or task.batch_id != batch_id or not task.image_path:
        raise HTTPException(status_code=404, detail="Изображение не найдено")
    file_path = get_storage().path_for(task.image_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл отсутствует на диске")
    return FileResponse(file_path, filename=f"{task.model_id}{file_path.suffix}")
