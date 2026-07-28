from __future__ import annotations

import asyncio
import json
import time
from urllib.parse import urlparse

import httpx

from app.config import get_settings
from app.db import SessionLocal
from app.kie_client import KieTaskResult, TERMINAL_STATES, get_kie_client
from app.models import GenerationBatch, GenerationTask
from app.registry import AspectPreset, Style, get_model
from app.schemas import GenerationCreateRequest
from app.storage import get_storage

settings = get_settings()


def create_batch(db, req: GenerationCreateRequest) -> GenerationBatch:
    batch = GenerationBatch(
        prompt=req.prompt,
        style=req.style.value,
        aspect_preset=req.aspect_preset.value,
        purpose=req.purpose,
        negative_prompt=req.negative_prompt,
        seed=req.seed,
        status="running",
    )
    db.add(batch)
    db.flush()

    for model_id in req.model_ids:
        db.add(GenerationTask(batch_id=batch.id, model_id=model_id, status="pending"))

    db.commit()
    db.refresh(batch)
    return batch


def start_batch_processing(batch_id: str) -> None:
    asyncio.create_task(run_batch(batch_id))


async def run_batch(batch_id: str) -> None:
    db = SessionLocal()
    try:
        batch = db.get(GenerationBatch, batch_id)
        if batch is None:
            return
        task_ids = [t.id for t in batch.tasks]
    finally:
        db.close()

    async with httpx.AsyncClient(timeout=90) as client:
        await asyncio.gather(*[_run_single_task(client, task_id) for task_id in task_ids])

    db = SessionLocal()
    try:
        _finalize_batch(db, batch_id)
    finally:
        db.close()


async def _run_single_task(client: httpx.AsyncClient, task_id: str) -> None:
    db = SessionLocal()
    try:
        task = db.get(GenerationTask, task_id)
        if task is None:
            return
        batch = task.batch
        spec = get_model(task.model_id)
        if spec is None:
            task.status = "failed"
            task.error = f"unknown model_id: {task.model_id}"
            db.commit()
            return

        task.status = "running"
        db.commit()

        kie = get_kie_client()
        try:
            input_payload = spec.build_input(
                batch.prompt,
                Style(batch.style),
                AspectPreset(batch.aspect_preset),
                batch.negative_prompt if spec.supports_negative_prompt else None,
                batch.seed if spec.supports_seed else None,
            )
            kie_task_id = await kie.create_task(client, spec.kie_model, input_payload)
            task.kie_task_id = kie_task_id
            db.commit()

            result = await _poll_until_done(client, kie, kie_task_id)

            task.cost_credits = result.credits_consumed
            task.duration_ms = result.duration_ms
            task.raw_response = json.dumps(result.raw)[:10000]

            if result.state == "success" and result.result_urls:
                image_resp = await client.get(result.result_urls[0])
                image_resp.raise_for_status()
                rel_path = f"{batch.id}/{task.id}{_guess_ext(result.result_urls[0])}"
                get_storage().save(rel_path, image_resp.content)
                task.image_path = rel_path
                task.status = "done"
            else:
                task.status = "failed"
                task.error = result.fail_msg or "generation failed without message"
        except Exception as exc:  # noqa: BLE001 - изолируем сбой одной модели от остальных
            task.status = "failed"
            task.error = str(exc)[:2000]

        db.commit()
    finally:
        db.close()


async def _poll_until_done(client: httpx.AsyncClient, kie, kie_task_id: str) -> KieTaskResult:
    deadline = time.monotonic() + settings.poll_timeout_seconds
    while True:
        result = await kie.get_task_result(client, kie_task_id)
        if result.state in TERMINAL_STATES:
            return result
        if time.monotonic() > deadline:
            return KieTaskResult(
                state="fail", result_urls=[], credits_consumed=None,
                duration_ms=None, fail_msg="timeout waiting for kie.ai", raw={},
            )
        await asyncio.sleep(settings.poll_interval_seconds)


def _guess_ext(url: str) -> str:
    suffix = "".join(urlparse(url).path.split(".")[-1:]) if "." in urlparse(url).path else ""
    if suffix and len(suffix) <= 5 and suffix.isalnum():
        return f".{suffix}"
    return ".jpg"


def _finalize_batch(db, batch_id: str) -> None:
    batch = db.get(GenerationBatch, batch_id)
    if batch is None:
        return
    tasks = db.query(GenerationTask).filter(GenerationTask.batch_id == batch_id).all()
    batch.total_cost_credits = sum(t.cost_credits or 0 for t in tasks)
    batch.status = "done" if any(t.status == "done" for t in tasks) else "failed"
    db.commit()
