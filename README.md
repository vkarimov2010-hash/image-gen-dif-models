# Сравнение моделей генерации изображений (kie.ai)

Промт и настройки задаются один раз, изображение генерируется параллельно
несколькими моделями через [kie.ai](https://kie.ai), результаты показываются
рядом для сравнения — со стоимостью и скачиванием.

## Запуск через Docker Compose (рекомендуется)

1. Скопировать `backend/.env.example` в `backend/.env` и вписать `KIE_API_KEY`.
2. `docker compose up --build`
3. Фронтенд: http://localhost:5173, бэкенд: http://localhost:8000/health

## Локальная разработка без Docker

Бэкенд (нужен Python 3.12, Postgres — можно поднять только `docker compose up -d db`):
```
cd backend
python -m venv .venv
./.venv/Scripts/activate  # Windows
pip install -r requirements.txt
cp .env.example .env  # указать DATABASE_URL на локальный Postgres и KIE_API_KEY
alembic upgrade head
uvicorn app.main:app --reload
```

Фронтенд:
```
cd frontend
npm install
npm run dev
```

## Добавление новой модели kie.ai

Всё в одном месте — `backend/app/registry.py`. Добавить `ModelSpec` с
`kie_model` (значением из документации kie.ai) и функцией `build_input`,
маппящей стиль/формат в параметры конкретной модели. Ни фронтенд, ни роутеры
менять не нужно — список моделей в UI подтягивается с `GET /models`.

## Структура

- `backend/` — FastAPI, SQLAlchemy, Alembic, интеграция с kie.ai
- `frontend/` — React + Vite + TypeScript
- `storage/` — локальное хранилище сгенерированных изображений (volume)

## Документация

- [`KIE_AI_INTEGRATION.md`](KIE_AI_INTEGRATION.md) — выжимка по API kie.ai:
  эндпоинты, нюансы парсинга ответа, схема ретраев, проверенный реальным
  ключом реестр моделей (стоимость, форматы вывода, особенности) и
  минимальный клиент на `httpx`.
