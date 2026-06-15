"""
ScamShield Backend API — entry point.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import db
from config import APP_TITLE, APP_VERSION, APP_DESCRIPTION, PLATFORM_WEBHOOKS
from models.schemas import HealthResponse
from routers import analyse, alerts, feedback

_start_time = time.monotonic()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    yield
    await db.close_pool()


app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyse.router)
app.include_router(alerts.router)
app.include_router(feedback.router)


@app.get("/health", response_model=HealthResponse, tags=["Meta"], summary="API health check")
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=APP_VERSION,
        nlp_backend="rule-based (plug-in model slot available)",
        platform_count=len(PLATFORM_WEBHOOKS),
        uptime_seconds=round(time.monotonic() - _start_time, 2),
    )


@app.get("/", tags=["Meta"], include_in_schema=False)
def root():
    return {
        "message": "ScamShield Backend API is running.",
        "docs": "/docs",
        "health": "/health",
    }
