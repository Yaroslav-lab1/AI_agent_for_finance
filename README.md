# Finance AI Agent

Рабочий fullstack-прототип для учёта личных финансов и импорта банковских операций через локальный deterministic AI-agent pipeline. Пользователь регистрируется, ведёт доходы и расходы, смотрит статистику и импортирует операции из текста, CSV или изображения. Агент создаёт только кандидатов на импорт, а реальные операции появляются в истории только после подтверждения пользователя.

## Архитектура

Backend реализован на FastAPI, SQLAlchemy 2 async и Alembic. Данные хранятся в PostgreSQL: пользователи, категории, транзакции, import jobs, import candidates и audit logs. Авторизация выполнена через JWT, все операции и импорты привязаны к владельцу. AI-слой разделён на инструменты чтения текста, CSV, OCR, нормализации, классификации и дедупликации; по умолчанию используется mock extractor без внешних API, а для реального разбора можно включить OpenAI-compatible LLM provider. Frontend на React + TypeScript + Vite предоставляет auth flow, dashboard, ручное добавление операций, фильтры, статистику, график и preview импортированных кандидатов.

## Быстрый запуск

```bash
cp .env.example .env
docker compose up --build
```

После старта:

- frontend: `http://localhost:5173`
- backend OpenAPI: `http://localhost:8000/docs`
- healthcheck: `http://localhost:8000/health`

Если порт backend `8000` уже занят, его можно переопределить:

```bash
BACKEND_PORT=8001 VITE_API_URL=http://localhost:8001/api docker compose up --build
```

Миграции можно выполнить отдельно:

```bash
docker compose exec backend alembic upgrade head
```

Backend также создаёт таблицы и системные категории при запуске в development/test режиме, чтобы демо открывалось сразу.

## Тесты

```bash
docker compose exec backend pytest
docker compose exec backend pytest --cov=app --cov-report=term-missing
```

Локально из `backend/`:

```bash
pip install -r requirements.txt
pytest
```

Frontend build:

```bash
docker compose exec frontend npm run build
```

## Переменные окружения

Основные настройки лежат в `.env.example`: `DATABASE_URL`, `JWT_SECRET`, `BACKEND_CORS_ORIGINS`, `OCR_LANG`, `MAX_UPLOAD_SIZE_MB`, `LLM_PROVIDER`. Реальные секреты не должны храниться в репозитории.

Для локального LLM-парсера через Ollama укажите в `.env`:

```env
LLM_PROVIDER=ollama
LLM_MODEL=qwen3.5:9b
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_REQUEST_TIMEOUT_SECONDS=120
```

`host.docker.internal` нужен, когда backend запущен в Docker, а Ollama работает на хостовой машине. Если запускаете backend без Docker, используйте `OLLAMA_BASE_URL=http://localhost:11434`.

Provider вызывает Ollama `/api/chat` со structured output через JSON Schema и ожидает строго:

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

Для OpenAI-compatible LLM вместо Ollama можно указать:

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1-mini
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
```

Если в уведомлении есть только время без даты, LLM получает текущую дату импорта и должен использовать её. Баланс, номера карт и технические номера игнорируются.

## Демо-сценарий

1. Откройте `http://localhost:5173`.
2. Зарегистрируйте `demo@example.com` / `demo-password-123`.
3. Добавьте расход `1200.00`, категория `Продукты`, комментарий `Покупка продуктов`.
4. Добавьте доход `100000.00`, категория `Зарплата`, комментарий `Зарплата`.
5. Проверьте доход, расход, баланс и график расходов.
6. Вставьте текст импорта:

```text
01.07.2026 Списание 349,90 RUB Перекрёсток
01.07.2026 Зачисление 5000,00 RUB Перевод от Иван
02.07.2026 Списание 220,00 RUB Метро
```

7. Проверьте 3 кандидата, отредактируйте один при необходимости и подтвердите выбранные.
8. Повторите импорт того же текста: кандидаты будут помечены как возможные/точные дубли.

## Ограничения прототипа

LLM-провайдер по умолчанию mock и не делает сетевых запросов. Реальный Ollama provider работает локально с моделью вроде `qwen3.5:9b`; OpenAI-compatible provider включается через `.env` и требует API key. OCR использует `pytesseract`, а в тестах мокается. Нет банковских API, бюджетов и production-инфраструктуры; модель import jobs готова к будущей асинхронной обработке.
