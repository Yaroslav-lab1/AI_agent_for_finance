# Легенда 3: База данных, миграции и окружение

## Роль

Участник отвечал за хранение данных, миграции и воспроизводимый запуск проекта через Docker Compose.

## Что сделал

- Настроил PostgreSQL 16 как основную базу данных проекта.
- Описал таблицы пользователей, категорий, операций, импортов, кандидатов и audit log.
- Добавил Alembic-миграции для воспроизводимого создания схемы БД.
- Настроил async-подключение backend к PostgreSQL через SQLAlchemy и asyncpg.
- Подготовил `docker-compose.yml` для запуска `postgres`, `backend` и `frontend`.
- Описал переменные окружения в `.env.example`: БД, JWT, CORS, LLM, Ollama, OpenAI-compatible API, OCR и upload-limit.
- Добавил Docker volume `postgres_data`, чтобы данные сохранялись между перезапусками контейнеров.
- Учел системную зависимость Tesseract OCR в backend-контейнере.

## Что может рассказать на защите

PostgreSQL выбран потому, что финансовые данные требуют целостности, транзакций и связей между таблицами. Docker Compose нужен для воспроизводимого запуска: не надо вручную поднимать БД, backend и frontend по отдельности.

## Какие файлы знает

- `docker-compose.yml`
- `.env.example`
- `backend/alembic.ini`
- `backend/alembic/versions/*.py`
- `backend/app/db/session.py`
- `backend/app/db/base.py`
- `backend/app/models/*.py`
- `backend/Dockerfile`

## Ответственность за качество

Проверял запуск контейнеров, применение миграций, доступность PostgreSQL, корректность `DATABASE_URL`, сохранение данных в volume и совместимость настроек с локальным запуском.
