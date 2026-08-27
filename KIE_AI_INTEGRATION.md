# Интеграция с kie.ai API (image generation)

Вытащено из проекта `image-gen-dif-models` (сервис сравнения моделей
генерации изображений). Всё ниже проверено вручную реальным API-ключом
kie.ai, кроме отдельно помеченного.

## 1. Базовые параметры

- Base URL: `https://api.kie.ai`
- Авторизация: заголовок `Authorization: Bearer <KIE_API_KEY>`
- Все запросы — JSON (`Content-Type: application/json`)
- API асинхронное: сначала создаёшь задачу (`createTask`), потом поллишь
  её статус (`recordInfo`), пока не получишь терминальное состояние.

## 2. Эндпоинты

### 2.1 Создание задачи генерации

```
POST /api/v1/jobs/createTask
Authorization: Bearer <KIE_API_KEY>
Content-Type: application/json

{
  "model": "flux-2/pro-text-to-image",
  "input": {
    "prompt": "a cat on a skateboard, photorealistic",
    "aspect_ratio": "1:1",
    "resolution": "1K"
  }
}
```

`input` — произвольный объект, схема параметров своя для каждой модели
(см. раздел 4). Модель указывается строкой в поле `model` верхнего уровня.

Успешный ответ:
```json
{ "code": 200, "data": { "taskId": "abc123..." } }
```

Проверка ответа: `code` не всегда строго 200 при рабочем сценарии — в
практике встречались и 500/505 с валидным `data.taskId` внутри, поэтому
надёжнее ориентироваться на наличие `data.taskId`, а не только на `code`.
Если `taskId` нет — считать ошибкой.

### 2.2 Получение статуса/результата задачи

```
GET /api/v1/jobs/recordInfo?taskId=abc123...
Authorization: Bearer <KIE_API_KEY>
```

Ответ:
```json
{
  "code": 200,
  "data": {
    "state": "success",            // waiting | queuing | generating | success | fail
    "resultJson": "{\"resultUrls\":[\"https://.../image.png\"]}",
    "creditsConsumed": 8,
    "costTime": 4123,
    "failMsg": null
  }
}
```

Важные нюансы парсинга:
- `resultJson` — это **строка** с вложенным JSON, а не объект — нужно
  делать `json.loads()` отдельно и доставать `resultUrls`.
- `data` в ответе может быть **явным `null`** (не отсутствовать как ключ),
  особенно на невалидных задачах — `payload.get("data", {})` в этом случае
  НЕ подставит дефолт (вернёт `None`). Нужно `payload.get("data") or {}`.
- Терминальные состояния — только `success` и `fail`. Всё остальное
  (`waiting`, `queuing`, `generating`) — поллить дальше.
- Реальная стоимость генерации — поле `creditsConsumed` в этом ответе.
  Оно и есть источник истины, а не любые ориентировочные оценки заранее.

Рекомендуемый интервал поллинга: 2 секунды, таймаут — 300 секунд (после
этого считать задачу зафейленной по таймауту на своей стороне).

### 2.3 Баланс кредитов аккаунта

```
GET /api/v1/chat/credit
Authorization: Bearer <KIE_API_KEY>
```

Возвращает текущий баланс кредитов аккаунта — полезно для бейджа
баланса в UI.

## 3. Обработка ошибок и ретраи

- Ретраить имеет смысл только `429, 500, 502, 503, 504` и сетевые сбои
  (transport errors) — это нестабильность инфраструктуры.
- Ошибки `4xx` (кроме 429) — не ретраить, они не исчезнут при повторе
  (невалидные параметры, авторизация и т.п.).
- Рекомендуемая схема: до 3 попыток, экспоненциальная/линейная задержка
  (в проекте использовалось `1.5s * номер_попытки`).
- **Известная нестабильность на стороне kie.ai** (не баг клиента): модели
  `google/imagen4`, `google/imagen4-ultra` и `ideogram/v3-text-to-image`
  неоднократно и воспроизводимо возвращали мгновенный (0–15 мс)
  `failCode: 500, "Internal Error, Please try again later."` без списания
  кредитов, при том что формат запроса к ним сверен с документацией и
  идентичен по структуре рабочим моделям (Flux-2 и др.). Если планируете
  использовать эти три модели — закладывайте отдельный ретрай именно на
  transient-фейл уровня уже принятой задачи (не только на HTTP-уровне),
  либо на первое время исключите их из списка активных.

## 4. Реестр моделей (актуальные проверенные данные)

Стоимость — **фактическая** (`creditsConsumed` из реального прогона), не
маркетинговая оценка. Курс кредитов в валюту нужно смотреть отдельно на
https://kie.ai/pricing (в проекте это не зафиксировано намертво — цены
kie.ai могут меняться, ориентируйтесь на `creditsConsumed` как на истину
в моменте).

| Модель (`model` в API) | Провайдер | Стоимость, кредиты | Формат/разрешение вывода | Особенности |
|---|---|---|---|---|
| `flux-2/pro-text-to-image` | Black Forest Labs | ~20 (оценка, не переподтверждалась после фикса остальных) | — | `aspect_ratio`, `resolution` |
| `gpt-image-2-text-to-image` | OpenAI | **6.0** | PNG 1254×1254 | `aspect_ratio`, `resolution` |
| `grok-imagine/text-to-image` | xAI | **4.0** | JPEG 960×960 | не поддерживает 4:3/3:4, только 1:1/3:2/2:3/9:16/16:9 |
| `seedream/5-lite-text-to-image` | ByteDance | **5.5** | JPEG 1920×1920 | `aspect_ratio`, `quality: "basic"` |
| `qwen2/text-to-image` | Alibaba | **5.6** | JPEG 2048×2048 | лимит промта ~800 символов (иначе createTask падает); поддерживает `seed` |
| `google/nano-banana` | Google | **4.0** | PNG 1024×1024 | только `prompt` + `aspect_ratio` |
| `nano-banana-2` | Google | **8.0** | PNG 1024×1024 | + `image_input: []`, `resolution`, `output_format` |
| `nano-banana-2-lite` | Google | **4.0** | JPEG 1024×1024 | только `prompt` + `aspect_ratio` |
| `z-image` | Tongyi-MAI | **0.8** | PNG 1536×1536 | `aspect_ratio` **обязателен** (createTask вернёт `500 "This field is required"` без него), `"auto"` не принимается |
| `google/imagen4` | Google | не подтверждена (нестабильна) | — | см. раздел 3, transient-фейлы |
| `google/imagen4-ultra` | Google | не подтверждена (нестабильна) | — | см. раздел 3, transient-фейлы |
| `ideogram/v3-text-to-image` | Ideogram | не подтверждена (нестабильна) | — | см. раздел 3, transient-фейлы |

Общие поддерживаемые параметры `input` в text-to-image моделях этого
семейства:
- `prompt` (string, всегда)
- `aspect_ratio` (string, формат `"W:H"`, например `"1:1"`, `"4:3"`,
  `"3:4"`, `"9:16"`, `"16:9"`) — у части моделей называется иначе
  (`image_size` у Ideogram/Qwen2 со своими enum-значениями типа
  `square_hd`, `landscape_4_3`)
- `negative_prompt` (string, опционально) — поддерживают не все модели
- `seed` (int или string в зависимости от модели, опционально) —
  поддерживают не все модели

## 5. Пример клиента (Python/httpx)

Минимальный переиспользуемый клиент — адаптация из
`backend/app/kie_client.py` этого проекта:

```python
import asyncio
import json
import httpx

BASE_URL = "https://api.kie.ai"
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
TERMINAL_STATES = {"success", "fail"}

class KieClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def create_task(self, client: httpx.AsyncClient, model: str, input_payload: dict) -> str:
        resp = await client.post(
            f"{BASE_URL}/api/v1/jobs/createTask",
            headers=self._headers(),
            json={"model": model, "input": input_payload},
        )
        resp.raise_for_status()
        data = resp.json()
        task_id = (data.get("data") or {}).get("taskId")
        if not task_id:
            raise RuntimeError(f"createTask failed: {data}")
        return task_id

    async def get_task_result(self, client: httpx.AsyncClient, task_id: str) -> dict:
        resp = await client.get(
            f"{BASE_URL}/api/v1/jobs/recordInfo",
            headers=self._headers(),
            params={"taskId": task_id},
        )
        resp.raise_for_status()
        payload = (resp.json().get("data")) or {}
        result_urls = []
        if payload.get("resultJson"):
            try:
                result_urls = json.loads(payload["resultJson"]).get("resultUrls", [])
            except (json.JSONDecodeError, TypeError):
                pass
        return {
            "state": payload.get("state", "waiting"),
            "result_urls": result_urls,
            "credits_consumed": payload.get("creditsConsumed"),
            "fail_msg": payload.get("failMsg"),
        }

    async def poll_until_done(self, client: httpx.AsyncClient, task_id: str,
                               interval: float = 2.0, timeout: float = 300.0) -> dict:
        import time
        deadline = time.monotonic() + timeout
        while True:
            result = await self.get_task_result(client, task_id)
            if result["state"] in TERMINAL_STATES:
                return result
            if time.monotonic() > deadline:
                return {"state": "fail", "fail_msg": "timeout", "result_urls": [], "credits_consumed": None}
            await asyncio.sleep(interval)

    async def get_credit_balance(self, client: httpx.AsyncClient) -> dict:
        resp = await client.get(f"{BASE_URL}/api/v1/chat/credit", headers=self._headers())
        resp.raise_for_status()
        return resp.json()


# Использование:
async def main():
    kie = KieClient(api_key="...")
    async with httpx.AsyncClient(timeout=90) as client:
        task_id = await kie.create_task(client, "z-image", {
            "prompt": "a cat on a skateboard",
            "aspect_ratio": "1:1",
        })
        result = await kie.poll_until_done(client, task_id)
        if result["state"] == "success":
            print(result["result_urls"], "cost:", result["credits_consumed"])
        else:
            print("failed:", result["fail_msg"])
```

## 6. Переменные окружения

```
KIE_API_KEY=your_kie_ai_api_key_here
KIE_BASE_URL=https://api.kie.ai
```

## 7. Что стоит перепроверить при переносе

- Актуальный курс кредитов kie.ai в валюту — смотреть live на
  https://kie.ai/pricing, в этом документе его нет намеренно (меняется).
  `creditsConsumed` из `recordInfo` — надёжный источник факта потраченного,
  а не оценка.
- Статус моделей Imagen 4 / Imagen 4 Ultra / Ideogram V3 на момент переноса
  — возможно, kie.ai уже починил нестабильность.
- Точная стоимость `flux-2/pro-text-to-image` не переподтверждалась на
  практике так же тщательно, как остальные 11 моделей (см. таблицу) —
  указанные 20 кредитов это первичная оценка, не факт из `creditsConsumed`.
