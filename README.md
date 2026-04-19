# FastAPI Calculator — Module 12 (JWT Auth + Calculation BREAD)

A JWT-authenticated REST API with full BREAD (Browse, Read, Edit, Add, Delete) operations on calculations. Backed by GitHub Actions CI/CD that runs integration tests against Postgres and pushes a Docker image to Docker Hub on every merge to `main`.

**Status:** 70 tests passing · 96% coverage · CI green · Image deployed to Docker Hub

## Features

### Authentication
- `POST /users/register` — create a new user (bcrypt-hashed password, uniqueness enforced at DB layer)
- `POST /users/login` — verify credentials and return a signed JWT bearer token (JSON body)
- `POST /users/token` — OAuth2-compatible login (form-encoded) for Swagger UI's Authorize button
- `GET /users/me` — echoes the authenticated user (sanity-check for the token)

### Calculation BREAD (all JWT-protected, all scoped to the calling user)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/calculations` | Add — creates a calculation, computes `result` via the Factory |
| GET | `/calculations` | Browse — lists the caller's calculations |
| GET | `/calculations/{id}` | Read — fetches one (404 if the caller doesn't own it) |
| PUT | `/calculations/{id}` | Edit — partial update, recomputes `result` |
| DELETE | `/calculations/{id}` | Delete — permanently removes it (`204 No Content`) |

### Security
- Passwords stored as bcrypt hashes (`$2b$...`) — never plaintext
- JWTs signed with HS256 using a secret loaded from `JWT_SECRET_KEY`
- Row-level authorization: users can only see and mutate their own calculations; cross-user requests return `404` to avoid leaking existence of other users' data
- `UserRead` response model guarantees `password_hash` is never serialized

### CI/CD
- GitHub Actions spins up a Postgres 16 service container, runs unit + integration tests with coverage, then on `main` builds and pushes the Docker image to Docker Hub (tagged `latest` + SHA) and scans it with Trivy

## Project Layout

```
app/
  main.py                  # FastAPI app, CORS, router registration
  db/database.py           # SQLAlchemy engine/session/Base
  models/
    user.py                # User model
    calculation.py         # Calculation model (FK to users)
  schemas/
    user.py                # UserCreate, UserLogin, UserRead, Token
    calculation.py         # CalculationCreate, CalculationUpdate, CalculationRead
  auth/
    hashing.py             # bcrypt hash_password / verify_password
    jwt.py                 # JWT helpers + get_current_user dependency
  routers/
    users.py               # /users/register, /users/login, /users/token, /users/me
    calculations.py        # BREAD endpoints
  operations/
    factory.py             # CalculationFactory (Add/Sub/Multiply/Divide)
tests/
  conftest.py              # Transactional DB + TestClient + auth_client fixtures
  unit/                    # No DB required (31 tests)
  integration/             # Real Postgres — users + calculations + BREAD (39 tests)
.github/workflows/ci.yml   # Test job + Docker Hub push job
Dockerfile
docker-compose.yml
requirements.txt
.env.example
```

## Running Locally

### Option A — Docker Compose (recommended)

```bash
cp .env.example .env
# edit .env and set JWT_SECRET_KEY
docker compose up --build
```

API available at `http://localhost:8000/docs`.

### Option B — Python + Postgres container

```bash
# Start Postgres
docker run -d --name fastapi-pg \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=fastapi_calc \
  -p 5432:5432 postgres:16

# Create the test DB (separate from the dev DB)
docker exec -i fastapi-pg psql -U postgres -c "CREATE DATABASE fastapi_calc_test;"

# Set up the app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")

# Run
uvicorn app.main:app --reload
```

## Running Tests

Full suite (unit + integration; Postgres required):
```bash
pytest --cov=app --cov-report=term-missing -v
```

Unit tests only (no DB):
```bash
pytest tests/unit -v
```

Integration tests only:
```bash
pytest tests/integration -v
```

Expected result: **70 passed** with **96% coverage**.

## Manual API Verification (OpenAPI / Swagger)

With the server running, open `http://localhost:8000/docs`.

1. **Register** — expand `POST /users/register`, click *Try it out*, and submit:
   ```json
   {"username": "demo", "email": "demo@example.com", "password": "strongpass1"}
   ```
2. **Authorize** — click the green **Authorize** button top-right, enter your username and password, and click Authorize. Swagger uses the `/users/token` endpoint under the hood.
3. **BREAD** — all calculation endpoints are now unlocked. Try them in order:
   - `POST /calculations` with `{"a": 6, "b": 7, "type": "Multiply"}` → 201 with `"result": 42`
   - `GET /calculations` → list of one
   - `GET /calculations/{id}` → the same record
   - `PUT /calculations/{id}` with `{"type": "Add"}` → 200, `result` recomputed to `13`
   - `DELETE /calculations/{id}` → 204, subsequent GET returns 404

## Docker Hub

```bash
docker pull gxutxm7/fastapi-calculator:latest
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+psycopg2://postgres:postgres@host.docker.internal:5432/fastapi_calc \
  -e JWT_SECRET_KEY=your-secret-here \
  gxutxm7/fastapi-calculator:latest
```

**Docker Hub repository:** https://hub.docker.com/r/gxutxm7/fastapi-calculator

## CI/CD — Required GitHub Secret

In repo Settings → Secrets and variables → Actions, add:

| Secret | Purpose |
|---|---|
| `DOCKERHUB_TOKEN` | Docker Hub Access Token (hub.docker.com → Account Settings → Security → New Access Token, Read/Write/Delete scope) |

The Docker Hub username (`gxutxm7`) is hardcoded in the workflow. The workflow file is `.github/workflows/ci.yml`. The `build-and-push` job only runs on `push` events to `main` so pull requests still run tests without pushing images.

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://postgres:postgres@localhost:5432/fastapi_calc` | SQLAlchemy connection string |
| `JWT_SECRET_KEY` | `dev-secret-change-me-in-production` | HMAC key used to sign JWTs. Generate a new value per environment. |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token lifetime in minutes |

Generate a production-grade secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
