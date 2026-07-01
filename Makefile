up:
	docker compose up --build

migrate:
	docker compose exec backend alembic upgrade head

test:
	docker compose exec backend pytest --cov=app --cov-report=term-missing

frontend-build:
	docker compose exec frontend npm run build
