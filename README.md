<div align="center">

# Teachka

### An all-in-one toolkit for teachers: grade calculators, group makers, live quizzes, and more, in one place.

[![Live](https://img.shields.io/badge/live-teachka.com-2ea44f?style=for-the-badge&logo=render&logoColor=white)](https://teachka.com)
[![CI](https://github.com/TokiSyt/teachkaProject/actions/workflows/ci.yml/badge.svg)](https://github.com/TokiSyt/teachkaProject/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-573%20passing-2ea44f)](#testing--quality)
[![Coverage](https://img.shields.io/badge/coverage-%E2%89%A570%25-2ea44f)](#testing--quality)

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](#)
[![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)](#)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql&logoColor=white)](#)
[![Tailwind](https://img.shields.io/badge/Tailwind-daisyUI-38BDF8?logo=tailwindcss&logoColor=white)](#)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](#)

**[Try it live](https://teachka.com)** &nbsp;·&nbsp; **[The tools](#the-tools)** &nbsp;·&nbsp; **[Architecture](#architecture-highlights)** &nbsp;·&nbsp; **[Run it locally](#run-it-locally)** &nbsp;·&nbsp; **[What I learned](#what-i-learned-building-this)**

</div>

---

## TL;DR for the busy reader

Teachka is a **production Django app** (live, multi-language, CI-gated) that bundles **8 classroom tools** behind one account. It is built to show clean, scalable backend architecture, not a toy CRUD demo.

What it demonstrates at a glance:

| | |
|---|---|
| **Modular monolith** | 8 self-contained Django apps over a shared `core` (base models, mixins, selectors) |
| **Real-time** | Live multiplayer quizzes over WebSockets (Django Channels + Redis) |
| **Internationalized** | Full EN / PT / CS translations via `i18n_patterns` + locale middleware |
| **Hardened** | CSP headers, brute-force lockout (django-axes), Django deploy-checklist gate in CI |
| **CI/CD** | 5-job pipeline: lint, typecheck, 573 tests (>=70% cov), dependency audit, deploy-check |
| **Real deploy** | Dockerised, shipped to Render with Postgres, Redis, WhiteNoise statics, and Cloudinary media |

---

## The tools

Each tool is an independent Django app. New tools drop in without touching the others.

| Tool | Route | What it does |
|------|-------|--------------|
| **Grade calculator** | `/grades/` | Weighted grade computation with a live, no-reload UI |
| **Group maker** | `/groups/` | Build and save reusable class / member lists |
| **Group divider** | `/divider/` | Split a group into teams, by team size **or** by number of teams |
| **Point / karma system** | `/karma/` | Track participation and behaviour points per member |
| **Wheel** | `/wheel/` | Random picker for cold-calling students |
| **Timer** | `/timer/` | Countdown and stopwatch for classroom activities |
| **Calendar** | `/calendar/` | Events, holidays, and week / day views |
| **Quizzmaker** | `/quizzes/` | Quiz authoring plus live, real-time multiplayer sessions |

> Tools share concepts where it makes sense. For example, groups created in **Group maker** automatically sync into the **Point system** through Django signals.

---

## Architecture highlights

<details open>
<summary><b>Modular app design</b></summary>

<br>

Every tool lives under `apps/` as its own Django app and is wired into the project URLs. A shared `apps/core` provides the reusable backbone:

- **Base models**: `TimestampedModel`, `UserOwnedModel`
- **Mixins**: `UserQuerySetMixin`, `UserOwnedMixin`, `FormUserMixin` (consistent ownership and auth across apps)
- **Context processors**: navigation shared to every template

This keeps each tool decoupled and independently testable, while avoiding duplicated boilerplate.

</details>

<details>
<summary><b>Service + Selector pattern (thin views)</b></summary>

<br>

Business logic stays out of views:

- **Selectors** (`selectors.py`): read paths and query optimization (`select_related` / `prefetch_related`)
- **Services** (`services/`): write paths and business operations

```python
# selectors.py - optimized reads
def get_group_full_data(group_id, user) -> dict: ...

# services/member_service.py - business logic
class MemberService:
    @staticmethod
    def update_member_data(member, positive_data, negative_data): ...
```

Views orchestrate; they do not compute.

</details>

<details>
<summary><b>Real-time live quizzes (Channels + Redis)</b></summary>

<br>

Quizzmaker runs **synchronous multiplayer quiz sessions** over WebSockets:

- **Django Channels** consumers manage host / player sessions and game state
- **Redis** is the channel layer broadcasting questions, answers, and scores in real time
- Served by **Daphne** (ASGI) alongside the standard request path

</details>

<details>
<summary><b>Internationalization</b></summary>

<br>

Full multilingual support (English, Portuguese, Czech) using `i18n_patterns` and `LocaleMiddleware`. The default language is unprefixed; others are served under a locale prefix. Translations live in `locale/` and compile to `.mo` at build time.

</details>

---

## Tech stack

| Layer | Choices |
|-------|---------|
| **Backend** | Python 3.12, Django 5.2, Django Channels (ASGI), Daphne |
| **Data** | PostgreSQL (`dj-database-url`), Redis (channel layer) |
| **Frontend** | Tailwind CSS + daisyUI, Lucide icons, crispy-forms, server-rendered templates |
| **Media / static** | Cloudinary (uploads), WhiteNoise (compressed static) |
| **Auth / security** | Custom user model, django-axes (lockout), CSP and security headers |
| **Tooling** | Ruff, mypy, pytest + factory-boy, Vitest (JS), pip-audit |
| **Infra** | Docker / Compose (dev), Render (prod), GitHub Actions (CI) |

---

## Testing & quality

The CI pipeline (`.github/workflows/ci.yml`) runs **5 independent jobs** on every PR:

| Job | What it enforces |
|-----|------------------|
| **lint** | `ruff check` plus `ruff format --check` |
| **typecheck** | `mypy` static typing |
| **test** | **573 tests** via pytest, **fails under 70% coverage** (Redis service spun up for live-quiz tests) |
| **audit** | `pip-audit` for known CVEs in dependencies |
| **deploy-check** | `manage.py check --deploy` with production-like settings, before anything merges |

JS is covered separately with **Vitest** (jsdom).

---

## Run it locally

> Everything runs in Docker. The stack is Postgres + Django (ASGI) + Redis, with Tailwind built separately.

<details open>
<summary><b>1. Start the stack</b></summary>

<br>

```bash
make up          # start Postgres, Django, Redis
make migrate     # apply migrations
```

App is then on `http://localhost:8000`.

</details>

<details>
<summary><b>2. Build the CSS (separate process)</b></summary>

<br>

```bash
make tailwind-dev      # watch mode (rebuild on change)
# or
make tailwind-build    # one-off production build
```

</details>

<details>
<summary><b>3. Common commands</b></summary>

<br>

```bash
make test              # all Python tests
make test-cov          # tests + coverage report
make test-js           # JS tests (Vitest)
make check             # ruff + mypy + tests
make ci                # full CI suite locally
make translations      # compile i18n .po into .mo
```

</details>

<details>
<summary><b>Environment variables</b></summary>

<br>

| Var | Purpose |
|-----|---------|
| `DEBUG` | Explicit on / off; defaults to dev unless `RENDER` is present |
| `SECRET_KEY` | Required when `DEBUG=False` |
| `DATABASE_URL` | Postgres in Docker, SQLite for deploy-checks |
| `REDIS_URL` | Channel layer for live quizzes |
| `CLOUDINARY_URL` | Enables Cloudinary media storage in production |

</details>

---

## Deployment notes

- **Stateless media**: Render's disk is ephemeral, so user uploads go to **Cloudinary**; static assets are compressed and served by **WhiteNoise**.
- **Production hardening**: a Django `check --deploy` gate, CSP and referrer-policy headers, plus `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` driven by environment.
- **Single settings file**, environment-driven, with no fragile per-env settings split.

---

## What I learned building this

Refactoring an initially tightly-coupled codebase into **decoupled apps over a shared core** made it dramatically more testable and easier to extend. Adding **real-time multiplayer** pushed me into ASGI, Channels and Redis. Standing up a **multi-job CI pipeline** and a real **Render deploy** taught me to catch production issues (CSP, ephemeral storage, env config) *before* they reach users, and to keep a clean git history through disciplined branching.

---

<div align="center">

**Built by Tiago Silva** &nbsp;·&nbsp; [teachka.com](https://teachka.com)

Star the repo if it is useful. Feedback always welcome.

</div>
