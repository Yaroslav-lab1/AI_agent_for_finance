# Легенда 3: База данных, Docker и окружение

## Роль

Участник отвечал за PostgreSQL, миграции, Docker Compose и переменные окружения.

## Что сделал

- Настроил PostgreSQL в `docker-compose.yml`.
- Описал подключение backend к БД через `DATABASE_URL`.
- Добавил Alembic-миграции для воспроизводимого создания таблиц.
- Настроил Docker Compose для backend, frontend и postgres.
- Описал `.env.example`, чтобы проект можно было поднять на другой машине.

## Что может рассказать на защите

Главный акцент: база хранится в Docker volume, схема создаётся миграциями, а пароль PostgreSQL нужен не для входа в приложение, а для технического подключения к БД.

## Какие файлы знает

- `docker-compose.yml`
- `.env.example`
- `backend/alembic/*`
- `backend/app/db/session.py`
- `backend/app/repositories/*.py`

## Ответственность за качество

Проверял запуск контейнеров, healthcheck PostgreSQL, применение миграций и доступность API после старта.

