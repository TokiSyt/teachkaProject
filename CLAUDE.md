# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stellax is a modular Django app hub that brings together practical tools in one platform. Each app handles distinct functionality (grade calculator, group maker, karma points, etc.) and can be developed independently.

## Commands (via Makefile)

```bash
# Docker
make build          # Build and start containers
make up             # Start containers in background
make up-dev         # Start with Tailwind watch mode
make down           # Stop containers
make restart        # Restart containers
make logs           # View web container logs
make status         # Show container status
make clean          # Remove containers, volumes, and cache
make rebuild        # Rebuild without cache

# Django
make shell          # Django shell
make bash           # Bash in web container
make dbshell        # PostgreSQL shell
make migrate        # Run migrations
make makemigrations # Create migrations
make createsuperuser
make collectstatic

# Code Quality
make lint           # Run ruff linter
make lint-fix       # Run ruff and fix issues
make format         # Format code with ruff
make typecheck      # Run mypy type checker
make test           # Run pytest
make test-file file=path/to/test.py  # Run specific test
make check          # Run lint, typecheck, and test

# Tailwind
make tailwind-install  # Install npm dependencies
make tailwind-build    # Build CSS for production
```

## Architecture

### Project Structure
- `stellaxBaseProject/` - Django project configuration
  - `settings/` - Split settings (base, development, production, test)
  - `urls.py`, `wsgi.py`, `asgi.py`
- `apps/` - All Django applications
  - `core/` - Shared utilities (models, mixins, context processors, exceptions)
  - `grade_calculator/` - Grade calculation tools
  - `group_maker/` - Group management
  - `point_system/` - Karma/points tracking with services and selectors
  - `group_divider/` - Group division tools
  - `wheel/`, `timer/` - Utility apps
  - `users/` - Custom user model
- `templates/` - Global templates (base.html, home.html)
- `static/` - Global static assets (CSS, images)
- `theme/` - Tailwind CSS theme app
- `logs/` - Application logs
- `conftest.py` - Root pytest fixtures

### Key Configuration
- **Settings**: Split into `base.py`, `development.py`, `production.py`, `test.py`
  - Auto-detects environment via `DJANGO_ENV` env var or `RENDER` presence
- **Custom User Model**: `apps.users.CustomUser` - always use `AUTH_USER_MODEL` setting
- **Database**: PostgreSQL via `dj_database_url` (uses `DATABASE_URL` env var)
- **Forms**: Uses crispy-forms with Bootstrap 4 template pack
- **Icons**: Lucide icons library integrated
- **CSS**: Tailwind CSS via `theme/` app, compiled CSS at `theme/static/css/dist/`
- **Static Files**: WhiteNoise middleware serves static files in production
- **Logging**: Configured in `settings/base.py`, logs to `logs/stellax.log`

### App Pattern
Each app in `apps/` follows Django conventions:
- `models.py`, `views.py`, `urls.py`, `forms.py`, `admin.py`
- `templates/<app_name>/` for app-specific templates
- `services/` directory for business logic
- `selectors.py` for optimized queries (see `point_system/`)
- `signals.py` for Django signals (see `group_maker/`)
- `tests/` directory with `factories.py`, `conftest.py`, `test_*.py`

### Core App (`apps/core/`)
Shared utilities across all apps:
- `models.py`: `TimestampedModel`, `UserOwnedModel` abstract base classes
- `mixins.py`: `UserQuerySetMixin`, `UserOwnedMixin`, `FormUserMixin`
- `context_processors.py`: Dynamic navigation for sidebar
- `exceptions.py`: Custom exception classes

### URL Routing
Apps are mounted at their respective paths in `stellaxBaseProject/urls.py`:
- `/grades/` - Grade Calculator
- `/groups/` - Group Maker
- `/karma/` - Karma Points (point_system)
- `/divider/` - Group Divider
- `/wheel/`, `/timer/` - Utility apps
- Auth URLs at root (login, logout via `django.contrib.auth.urls`)
- Admin at `/admin/`

### Testing
- Uses pytest with pytest-django
- Factory Boy for test data
- Root `conftest.py` with shared fixtures (`user`, `authenticated_client`, `other_user`)
- App-specific fixtures in `apps/<app>/tests/conftest.py`
- Run tests: `make test` or `pytest`

## Deployment

Deployed to Render using ASGI:
```bash
python -m gunicorn stellaxBaseProject.asgi:application -k uvicorn.workers.UvicornWorker
```

Environment variables needed:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Django secret key
- `RENDER` - Set when running on Render (selects production settings)
- `DJANGO_ENV` - Optional: `development`, `production`, or `test`
