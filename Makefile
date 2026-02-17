.PHONY: build up down restart logs shell dbshell migrate createsuperuser translations collectstatic test clean lint typecheck format tailwind

# Build and start containers
build:
	docker compose up --build

up:
	docker compose up

# Start containers in background
up-d:
	docker compose up -d

# Stop containers
down:
	docker compose --profile dev down

# Restart containers
restart:
	docker compose down
	docker compose up -d

# View logs
logs:
	docker compose logs -f web

# Open shell in web container
shell:
	docker compose exec web python manage.py shell

# Open bash in web container
bash:
	docker compose exec web /bin/bash

# Open PostgreSQL shell
dbshell:
	docker compose exec db psql -U postgres -d teachkadb

# Run migrations (creates and applies)
migrate:
	docker compose exec web python manage.py makemigrations
	docker compose exec web python manage.py migrate

# Create superuser
createsuperuser:
	docker compose exec web python manage.py createsuperuser

# Compile translation files (.po -> .mo)
translations:
	docker compose exec web python manage.py compilemessages

# Collect static files
collectstatic:
	docker compose exec web python manage.py collectstatic --no-input

# Run tests with pytest
test:
	docker compose exec web pytest

# Run tests with coverage report
test-cov:
	docker compose exec web pytest --cov=apps --cov-report=term-missing

# Run specific test file
test-file:
	docker compose exec web pytest $(file)

# Run linter
ruff:
	docker compose exec web ruff check .

# Run linter and fix issues
ruff-fix:
	docker compose exec web ruff check --fix .

# Run type checker (mypy)
mypy:
	docker compose exec web mypy .

# Format code with ruff
format:
	docker compose exec web ruff format .

# Build Tailwind CSS
tailwind-build:
	docker compose exec web sh -c "cd /app/theme/static_src && npm run build"

# Install Tailwind dependencies
tailwind-install:
	docker compose exec web sh -c "cd /app/theme/static_src && npm install"

# Watch Tailwind CSS changes (development) 
tailwind-dev:
	docker-compose run --rm web sh -c "cd theme/static_src && npm run dev"

# Run all checks (lint, typecheck, test)
check:
	docker compose exec web ruff check .
	docker compose exec web mypy .
	docker compose exec web pytest

# Clean up containers, volumes, and cached files
clean:
	docker compose --profile dev down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Rebuild without cache
rebuild:
	docker compose build --no-cache
	docker compose up -d

# Show container status
status:
	docker compose ps

# Run all CI checks (ruff, mypy, tests)
ci:
	docker compose exec web ruff check . --fix
	docker compose exec web ruff format .
	docker compose exec web mypy .
	docker compose exec web pytest