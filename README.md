# Finance AI Agent

Fullstack-приложение для учета личных финансов с AI-импортом банковских операций. Пользователь регистрируется, ведет доходы и расходы, смотрит статистику, импортирует операции из текста, CSV или изображения и подтверждает найденные AI-кандидаты перед сохранением в историю.

## Возможности

- Регистрация и вход по email/password через JWT.
- Личный кабинет: изменение имени, логина, email и пароля. Любое изменение профиля требует ввода актуального пароля.
- Ручное добавление доходов и расходов.
- Список операций с фильтрами по датам, типу, категории и поиску.
- Сортировка операций кликом по заголовкам таблицы: дата, тип, сумма, категория, комментарий, источник.
- Ограничение ширины комментария в таблице, чтобы длинные комментарии не растягивали строку.
- Статистика: общий доход, расход и баланс.
- Две диаграммы расходов по категориям: за все время и за выбранный месяц.
- AI-импорт из текста, CSV и изображений.
- OCR для скриншотов через Pillow + Tesseract.
- Предпросмотр кандидатов импорта, редактирование кандидатов, проверка дублей и подтверждение выбранных операций.

## Архитектура

Frontend: React + TypeScript + Vite, TanStack Query, Axios, Recharts.

Backend: Python 3.12, FastAPI, Pydantic, SQLAlchemy 2 async, Alembic, asyncpg.

Database: PostgreSQL 16.

AI/OCR pipeline:

1. `TextInputTool`, `CsvInputTool` или `ImageOcrTool` приводят входной источник к тексту.
2. LLM-клиент возвращает structured output по JSON Schema.
3. Инструменты нормализуют сумму и дату.
4. Определяются тип операции и категория.
5. Проверяются возможные дубли.
6. Результат сохраняется как `import_candidates`; финальные `transactions` создаются только после подтверждения пользователем.

Основные таблицы PostgreSQL:

- `users`
- `categories`
- `transactions`
- `import_jobs`
- `import_candidates`
- `agent_audit_logs`

## Быстрый запуск

```bash
cp .env.example .env
docker compose up --build
```

После старта:

- frontend: `http://localhost:5173`
- backend OpenAPI: `http://localhost:8000/docs`
- healthcheck: `http://localhost:8000/health`
- PostgreSQL: `localhost:5432`

Если порт backend `8000` занят:

```bash
BACKEND_PORT=8001 VITE_API_URL=http://localhost:8001/api docker compose up --build
```

Миграции отдельно:

```bash
docker compose exec backend alembic upgrade head
```

Backend при запуске выполняет миграции, а в development/test режиме также создает системные категории.

## Переменные окружения

Основные настройки лежат в `.env.example`:

- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- `BACKEND_CORS_ORIGINS`
- `LLM_PROVIDER`, `LLM_MODEL`
- `OLLAMA_BASE_URL`, `OLLAMA_REQUEST_TIMEOUT_SECONDS`
- `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_REQUEST_TIMEOUT_SECONDS`
- `OCR_LANG`
- `MAX_UPLOAD_SIZE_MB`
- `ENVIRONMENT`

Также `docker-compose.yml` поддерживает `BACKEND_PORT`, `FRONTEND_PORT` и `VITE_API_URL` для переопределения портов и адреса API на frontend.

Реальные секреты не нужно хранить в репозитории.

## LLM-настройки

По умолчанию используется mock-провайдер:

```env
LLM_PROVIDER=mock
LLM_MODEL=mock
```

Для локальной Ollama:

```env
LLM_PROVIDER=ollama
LLM_MODEL=qwen3.5:9b
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_REQUEST_TIMEOUT_SECONDS=120
```

`host.docker.internal` нужен, когда backend запущен в Docker, а Ollama работает на хостовой машине. Если backend запускается без Docker, используйте:

```env
OLLAMA_BASE_URL=http://localhost:11434
```

Для OpenAI-compatible API:

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1-mini
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
```

OpenRouter можно подключить через тот же OpenAI-compatible режим:

```env
LLM_PROVIDER=openai
LLM_MODEL=<openrouter-model-id>
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

LLM должен вернуть JSON по схеме:

```json
{
  "transactions": [
    {
      "amount": "359.00",
      "date": "2026-07-01",
      "operation_type": "expense",
      "category": "restaurants",
      "comment": "Rostics_74022053",
      "confidence": "0.90"
    }
  ]
}
```

Если в уведомлении есть только время без даты, агент использует дату импорта как опорную дату. Баланс, номера карт и технические номера уведомлений игнорируются.

## OCR и файлы

Поддержаны:

- текстовые банковские уведомления;
- CSV-файлы;
- изображения `.png`, `.jpg`, `.jpeg`, `.webp`.

В Docker backend устанавливает `tesseract-ocr` и `tesseract-ocr-rus`. Язык OCR задается через:

```env
OCR_LANG=rus+eng
```

Максимальный размер файла:

```env
MAX_UPLOAD_SIZE_MB=10
```

## API

Основные endpoint-ы:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `PATCH /api/auth/me`
- `GET /api/categories`
- `GET /api/transactions`
- `POST /api/transactions`
- `PUT /api/transactions/{transaction_id}`
- `DELETE /api/transactions/{transaction_id}`
- `GET /api/stats/summary`
- `GET /api/stats/expenses-by-category`
- `POST /api/imports/text`
- `POST /api/imports/csv`
- `POST /api/imports/image`
- `GET /api/imports/{job_id}`
- `PATCH /api/imports/candidates/{candidate_id}`
- `POST /api/imports/{job_id}/confirm`

`/api/stats/summary` и `/api/stats/expenses-by-category` принимают `date_from` и `date_to`, поэтому frontend строит статистику как за все время, так и за выбранный месяц.

## Тесты

Через Docker:

```bash
docker compose exec backend pytest
docker compose exec backend pytest --cov=app --cov-report=term-missing
docker compose exec frontend npm run build
```

Локально:

```bash
cd backend
pip install -r requirements.txt
pytest
```

Frontend:

```bash
cd frontend
npm install
npm run build
```

## Демо-сценарий

1. Откройте `http://localhost:5173`.
2. Зарегистрируйте пользователя, например `demo@example.com` / `demo-password-123`.
3. Откройте “Профиль” и проверьте, что имя, логин, email и пароль можно изменить только с вводом текущего пароля.
4. Добавьте расход вручную.
5. Добавьте доход вручную.
6. Проверьте карточки дохода, расхода и баланса.
7. Проверьте две диаграммы расходов: за все время и за выбранный месяц.
8. Отсортируйте таблицу операций кликом по заголовкам.
9. Вставьте текст для AI-импорта:

```text
01.07.2026 Списание 349,90 RUB Перекрёсток
01.07.2026 Зачисление 5000,00 RUB Перевод от Иван
02.07.2026 Списание 220,00 RUB Метро
```

10. Нажмите “Распознать”.
11. Проверьте кандидатов, отредактируйте их при необходимости и подтвердите выбранные.
12. Повторите импорт того же текста: кандидаты будут помечены как возможные или точные дубли.
13. Повторите импорт через CSV или изображение.

## Ограничения прототипа

- По умолчанию LLM-провайдер mock и не делает сетевых запросов.
- Реальный LLM включается через `.env`.
- OCR зависит от качества изображения и установленного Tesseract.
- Нет банковских API, бюджетов, фоновой очереди импортов и production-инфраструктуры.
- `import_jobs` уже отделены от финальных операций, поэтому проект готов к будущей асинхронной обработке импортов.
