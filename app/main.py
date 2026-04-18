"""FastAPI application entrypoint wiring user + calculation routers."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import Base, engine
from app.models.user import User  # noqa: F401  (register table)
from app.models.calculation import Calculation  # noqa: F401  (register table)
from app.routers import calculations, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (dev/test only; use Alembic in prod).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="FastAPI Calculator + Users (Module 11)",
    description="User registration/login with JWT + full BREAD for calculations.",
    version="0.11.0",
    lifespan=lifespan,
)

# CORS — tighten the allowed origins list for production deployments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}


app.include_router(users.router)
app.include_router(calculations.router)
