.PHONY: build up down restart logs shell dbshell migrate createsuperuser translations collectstatic test clean lint typecheck format tailwind deploy-check audit ci sync-holidays sync-holidays-intl sync-holidays-cz sync-holidays-pt sync-holidays-en

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

# Run JavaScript tests with Vitest
test-js:
	docker compose exec web sh -c "cd /app && npm install --silent && npm test"

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

# Django production deployment checklist (requires stack up: make up / up-d).
# Uses a placeholder SECRET_KEY only to validate settings; never use in production.
deploy-check:
	docker compose exec web env DEBUG=false \
		SECRET_KEY=ci-deploy-check-not-for-production-use-50chars-minimum-xxxxx \
		DATABASE_URL=sqlite:////tmp/teachka_deploy_check.sqlite3 \
		python manage.py check --deploy

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

# Audit dependencies for known CVEs
# Ignored:
#   GHSA-6w46-j5rx-g56g: pytest 8 dev-tool CVE; bump to 9 blocked by apps.calendar shadowing stdlib calendar
audit:
	docker compose exec -e XDG_CACHE_HOME=/tmp/pip-audit-cache web pip-audit -r requirements.txt --ignore-vuln GHSA-6w46-j5rx-g56g

# Sync holidays for the given year. Override with: make sync-holidays year=2027
year ?= 2026

sync-holidays:
	docker compose exec web python manage.py sync_holidays --year $(year)

sync-holidays-intl:
	docker compose exec web python manage.py sync_holidays --year $(year) --country INTL

sync-holidays-cz:
	docker compose exec web python manage.py sync_holidays --year $(year) --country CZ

sync-holidays-pt:
	docker compose exec web python manage.py sync_holidays --year $(year) --country PT

sync-holidays-en:
	docker compose exec web python manage.py sync_holidays --year $(year) --country EN

# Run all CI checks (ruff, mypy, tests, audit, Django deploy checklist)
ci:
	docker compose exec web ruff check .
	docker compose exec web ruff format .
	docker compose exec web mypy .
	docker compose exec web pytest --cov --cov-fail-under=70
	$(MAKE) audit
	$(MAKE) deploy-check