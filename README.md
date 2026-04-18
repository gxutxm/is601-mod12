# FastAPI Calculator — Module 11 (User Auth + Calculation BREAD)

Builds on Modules 8 and 10 by adding a JWT-protected REST API for user registration/login and full BREAD operations (Browse, Read, Edit, Add, Delete) on calculations. Backed by GitHub Actions CI/CD that runs an integration test suite against Postgres and pushes a Docker image to Docker Hub on every merge to `main`.

## Feature Summary

### Authentication
- `POST /users/register` — create a new user (bcrypt-hashed password, uniqueness enforced at the DB layer).
- `POST /users/login` — verify credentials and return a signed JWT bearer token.
- `GET /users/me` — echoes the authenticated user (sanity-check for the token).
- `app/auth/jwt.py` — `create_access_token`, `decode_access_token`, and the `get_current_user` FastAPI dependency.

### Calculation BREAD (all JWT-protected, all scoped to the calling user)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/calculations` | Add — creates a calculation, computes `result` via the Factory |
| GET | `/calculations` | Browse — lists the caller's calculations |
| GET | `/calculations/{id}` | Read — fetches one (404 if the caller doesn't own it) |
| PUT | `/calculations/{id}` | Edit — partial update, recomputes `result` |
| DELETE | `/calculations/{id}` | Delete — permanently removes it (`204 No Content`) |

### Security
- Passwords stored as bcrypt hashes (`$2b$...`) — never plaintext.
- JWTs signed with HS256 using a secret loaded from `JWT_SECRET_KEY`.
- Row-level authorization: users can only see and mutate their own calculations; cross-user requests return `404` (which avoids leaking existence of other users' data).
- `UserRead` response model guarantees `password_hash` is never serialized.

### CI/CD
- GitHub Actions spins up a Postgres 16 service container, runs unit + integration tests with coverage, then on `main` builds and pushes the Docker image to Docker Hub (with `latest` and SHA tags) and scans it with Trivy.

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
    users.py               # /users/register, /users/login, /users/me
    calculations.py        # BREAD endpoints
  operations/
    factory.py             # CalculationFactory (Add/Sub/Multiply/Divide)
tests/
  conftest.py              # Transactional DB + TestClient + auth_client fixtures
  unit/                    # No DB required
  integration/             # Real Postgres — users + calculations + BREAD coverage
.github/workflows/ci.yml   # Test job + Docker Hub push job
Dockerfile
docker-compose.yml
requirements.txt
.env.example
REFLECTION.md
```

## Running Locally

### Option A — Docker Compose (recommended)

```bash
cp .env.example .env
# edit JWT_SECRET_KEY
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

## Manual API Verification (OpenAPI / Swagger)

With the server running, open `http://localhost:8000/docs`.

1. **Register** — expand `POST /users/register`, click *Try it out*, and submit:
   ```json
   {"username": "demo", "email": "demo@example.com", "password": "strongpass1"}
   ```
2. **Login** — expand `POST /users/login`, submit the same username/password, and copy the `access_token` from the response.
3. **Authorize** — click the green **Authorize** button at the top right, paste the token, and submit. The lock icons on all calculation endpoints will close.
4. **BREAD** — use the calculation endpoints in order:
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

## CI/CD — Required GitHub Secrets

In repo Settings → Secrets and variables → Actions:

| Secret | Purpose |
|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub account (`gxutxm7`) |
| `DOCKERHUB_TOKEN` | Docker Hub Access Token (Account Settings → Security → New Access Token) |

The workflow file is `.github/workflows/ci.yml`. The `build-and-push` job only runs on `push` events to `main` so pull requests still run tests without pushing images.

## Reflection

See `REFLECTION.md` for a write-up of challenges encountered during development and deployment.
