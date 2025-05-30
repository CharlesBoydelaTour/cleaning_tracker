# Cleaning Tracker — API

Back-end service for the **Cleaning Tracker** application.
Built with **FastAPI**, **PostgreSQL (Supabase)**, and **uv** for lightning-fast dependency management.
It exposes a JSON/REST interface consumed by the React Native + Expo front-end and drives scheduled jobs (Celery / Edge Functions) that create recurring task occurrences and dispatch push / email reminders.

---

## 🏗 Project structure

```markdown
api/
├── .env.example            # template for local secrets
├── pyproject.toml          # dependencies (managed by uv)
├── uv.lock                 # deterministic lockfile
└── app/
    ├── __init__.py
    ├── main.py             # FastAPI instance & router mounting
    ├── config.py           # Pydantic BaseSettings
    ├── core/
    │   ├── database.py     # asyncpg connection pool helpers
    │   ├── security.py     # JWT / password hashing
    │   └── celery_app.py   # Celery factory
    ├── routers/            # HTTP endpoints
    │   ├── auth.py
    │   ├── households.py
    │   ├── tasks.py
    │   └── occurrences.py
    ├── schemas/            # Pydantic request / response models
    ├── services/           # domain logic (recurrence engine, notifications)
    ├── worker/             # background jobs → celery tasks
    └── tests/              # pytest & httpx-async test suites
```

---

## 🧰 Tech stack

| Purpose            | Library / Tool                                          |
| ------------------ | ------------------------------------------------------- |
| Web framework      | **FastAPI 0.111+**                                      |
| Async DB access    | **asyncpg**, **Supabase Python client**                 |
| Object validation  | **Pydantic v2**                                         |
| Background jobs    | **Celery 6** (or Supabase **Edge Functions** in Python) |
| Schedules / cron   | **APScheduler 4** or **Celery beat**                    |
| Task queues        | **Redis** (local) • **Cloud Run Jobs** (prod)           |
| Dependency manager | **uv**                                                  |
| Tests              | **pytest** • **pytest-asyncio** • **httpx**             |
| Lint & style       | **ruff** • **black**                                    |
| CI / CD            | **GitHub Actions** + `supabase db push` + Dockerfile    |

---

## 🚀 Quick-start

### 1 · Clone & install

```bash
git clone https://github.com/your-org/cleaning-tracker.git
cd cleaning-tracker/api

# install uv once (Linux / macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh

uv sync        # creates .venv and installs deps pinned in uv.lock
```

### 2 · Configure secrets

```bash
cp .env.example .env        # then fill in SUPABASE_URL, SERVICE_ROLE_KEY, etc.
```

### 3 · Run the API locally

```bash
uv run uvicorn app.main:app --reload --port 8000
```

API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger) and `/redoc`.

### 4 · Unit tests

```bash
uv run pytest -q
```

---

## ⚙️ Database workflow

| Action                            | Command                                |
| --------------------------------- | -------------------------------------- |
| Create a new migration            | `supabase migration new <name>`        |
| Apply migrations locally          | `supabase db reset`                    |
| Push migrations to Supabase cloud | `supabase db push --remote production` |

> **Tip**: keep the database schema **source-controlled** under `supabase/migrations/`.

---

## 🔄 Background services

| Service       | Local start command                          |
| ------------- | -------------------------------------------- |
| Celery worker | `uv run celery -A app.worker worker -l info` |
| Celery beat   | `uv run celery -A app.worker beat  -l info`  |

---

## 🌐 Environment variables (excerpt)

| Key                 | Sample value                        | Purpose                                  |
| ------------------- | ----------------------------------- | ---------------------------------------- |
| `SUPABASE_URL`      | `https://xyzcompany.supabase.co`    | PostgREST API & auth                     |
| `SERVICE_ROLE_KEY`  | `eyJhbGci...`                       | Supabase service JWT (server-side calls) |
| `DATABASE_URL`      | `postgresql+asyncpg://postgres:...` | direct Postgres access                   |
| `REDIS_URL`         | `redis://localhost:6379/0`          | Celery broker / result backend           |
| `EXPO_ACCESS_TOKEN` | *token*                             | to send push notifications               |

See **.env.example** for the full list.

---

## 📌 MVP Sprint 1 — API TODO (checklist)

* [x] **Bootstraper le dossier `api/`** avec uv & FastAPI
* [x] **Connexion Supabase / Postgres** et helpers `database.py`
* [ ] **Endpoints Auth** (`/auth/signup`, `/auth/login`, `/auth/refresh`)
* [ ] **Routes households** (create / join)
* [ ] **CRUD Catalogue & Tâches personnalisées** (`/tasks`, `/catalog`)
* [ ] **Service de récurrence** : RRULE ➜ `task_occurrences`
* [ ] **Endpoint Snooze** (`/occurrences/{id}/snooze`)
* [ ] **Notifications service** (Expo push, Resend email template)
* [ ] **Schema‐based unit tests** + E2E flow (httpx)
* [ ] **GitHub Actions pipeline**: lint → tests → db push → build Docker image

---

## 🤝 Contributing

1. Fork → create branch (`feat/my-feature`).
2. `uv sync` then code & add tests.
3. Ensure `ruff` & `black` pass (`uv run ruff check .`).
4. PR, wait for CI to be green, request review.

---

## 📝 License

MIT — see `LICENSE` in the monorepo root.

Happy cleaning & coding !
