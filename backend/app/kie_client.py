"""Клиент к унифицированному API kie.ai (createTask / recordInfo / credit).

Форматы запросов/ответов — по документации docs.kie.ai (market/quickstart,
market/common/get-task-detail). Реальный ключ нужен для проверки на практике;
при расхождениях в форматах ответа поправить парсинг здесь — это единственное
место, которое знает о деталях протокола kie.ai.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Awaitable, Callable, TypeVar

import httpx

from app.config import get_settings

settings = get_settings()

TERMINAL_STATES = {"success", "fail"}

T = TypeVar("T")

# Ретраим только нестабильные сетевые сбои и 5xx — ошибки клиента (400/401/422 и т.п.)
# не исчезнут при повторе, поэтому не ретраим их.
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 3
_RETRY_BACKOFF_SECONDS = 1.5


class KieApiError(RuntimeError):
    pass


async def _with_retries(call: Callable[[], Awaitable[T]]) -> T:
    last_exc: Exception | None = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            return await call()
        except httpx.HTTPStatusError as exc:
            last_exc = exc
            if exc.response.status_code not in _RETRYABLE_STATUS or attempt == _MAX_ATTEMPTS:
                raise
        except httpx.TransportError as exc:
            last_exc = exc
            if attempt == _MAX_ATTEMPTS:
                raise
        await asyncio.sleep(_RETRY_BACKOFF_SECONDS * attempt)
    raise last_exc  # pragma: no cover - недостижимо, для типизации


@dataclass
class KieTaskResult:
    state: str  # waiting | queuing | generating | success | fail
    result_urls: list[str]
    credits_consumed: float | None
    duration_ms: int | None
    fail_msg: str | None
    raw: dict


class KieClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or settings.kie_api_key
        self.base_url = (base_url or settings.kie_base_url).rstrip("/")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def create_task(self, client: httpx.AsyncClient, model: str, input_payload: dict) -> str:
        async def _call() -> httpx.Response:
            resp = await client.post(
                f"{self.base_url}/api/v1/jobs/createTask",
                headers=self._headers(),
                json={"model": model, "input": input_payload},
            )
            resp.raise_for_status()
            return resp

        resp = await _with_retries(_call)
        data = resp.json()
        if data.get("code") not in (200, 505, 500) or "data" not in data:
            raise KieApiError(f"createTask failed: {data}")
        task_id = data["data"].get("taskId")
        if not task_id:
            raise KieApiError(f"createTask response missing taskId: {data}")
        return task_id

    async def get_task_result(self, client: httpx.AsyncClient, task_id: str) -> KieTaskResult:
        async def _call() -> httpx.Response:
            resp = await client.get(
                f"{self.base_url}/api/v1/jobs/recordInfo",
                headers=self._headers(),
                params={"taskId": task_id},
            )
            resp.raise_for_status()
            return resp

        resp = await _with_retries(_call)
        data = resp.json()
        payload = data.get("data", {})
        state = payload.get("state", "waiting")

        result_urls: list[str] = []
        result_json_raw = payload.get("resultJson")
        if result_json_raw:
            try:
                parsed = json.loads(result_json_raw)
                result_urls = parsed.get("resultUrls", [])
            except (json.JSONDecodeError, TypeError):
                pass

        return KieTaskResult(
            state=state,
            result_urls=result_urls,
            credits_consumed=payload.get("creditsConsumed"),
            duration_ms=payload.get("costTime"),
            fail_msg=payload.get("failMsg") or None,
            raw=payload,
        )

    async def get_credit_balance(self, client: httpx.AsyncClient) -> dict:
        resp = await client.get(
            f"{self.base_url}/api/v1/chat/credit",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()


def get_kie_client() -> KieClient:
    return KieClient()
