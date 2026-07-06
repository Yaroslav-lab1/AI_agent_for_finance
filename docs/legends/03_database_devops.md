# Легенда 3: База данных, миграции и окружение

## Роль

Участник отвечал за хранение данных, миграции, переменные окружения и воспроизводимый запуск проекта через Docker Compose.

## Что сделал

- Настроил PostgreSQL 16 как основную базу данных проекта.
- Описал таблицы пользователей, категорий, операций, заданий импорта, кандидатов и audit log.
- Добавил Alembic-миграции для воспроизводимого создания схемы БД.
- Настроил async-подключение backend к PostgreSQL через SQLAlchemy и asyncpg.
- Подготовил `docker-compose.yml` для запуска `postgres`, `backend` и `frontend`.
- Описал переменные окружения в `.env.example`: БД, JWT, CORS, LLM, Ollama, OpenAI-compatible API, OCR и upload-limit.
- Добавил Docker volume `postgres_data`, чтобы данные сохранялись между перезапусками контейнеров.
- Учел системную зависимость Tesseract OCR в backend-контейнере: `tesseract-ocr` и `tesseract-ocr-rus`.
- Настроил healthcheck PostgreSQL, чтобы backend стартовал после готовности БД.

## Что может рассказать на защите

PostgreSQL выбран потому, что финансовые данные требуют целостности, транзакций и связей между таблицами. Docker Compose нужен для воспроизводимого запуска: не надо вручную поднимать БД, backend и frontend по отдельности.

Отдельно можно объяснить, что пароль PostgreSQL - это пароль технического пользователя БД, а не пароль пользователя приложения. Пользовательские пароли хранятся отдельно в виде `bcrypt`-хешей.

## Какие файлы знает

- `docker-compose.yml`
- `.env.example`
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `backend/alembic.ini`
- `backend/alembic/versions/*.py`
- `backend/app/db/session.py`
- `backend/app/db/base.py`
- `backend/app/models/*.py`
- `backend/app/repositories/categories.py`

## Ответственность за качество

Проверял запуск контейнеров, применение миграций, доступность PostgreSQL, корректность `DATABASE_URL`, сохранение данных в volume, установку OCR-зависимостей в backend-контейнере и совместимость настроек с локальным запуском.

## Возможный вопрос на защите

**Почему не SQLite?**

SQLite проще для тестов, но основному приложению нужны роли, внешние ключи, транзакционность, нормальный Docker-сервис и более реалистичная БД для финансовых данных. Поэтому в production-like окружении используется PostgreSQL, а SQLite оставлен только для быстрых backend-тестов.
