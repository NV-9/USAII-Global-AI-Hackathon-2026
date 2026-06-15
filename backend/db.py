"""
Database connection pool and schema management.

Uses asyncpg directly (no ORM) — the schema is small enough that raw SQL is
clearer than the overhead of SQLAlchemy async sessions for a two-table design.

The pool is initialised once at startup via the FastAPI lifespan handler and
shared across all requests as a module-level singleton.
"""

from __future__ import annotations

import json
import logging

import asyncpg

from config import DATABASE_URL

log = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS alerts (
    alert_id          TEXT        PRIMARY KEY,
    analysis_id       TEXT        NOT NULL,
    risk_score        INTEGER     NOT NULL,
    risk_level        TEXT        NOT NULL,
    platform_results  JSONB       NOT NULL,
    total_platforms   INTEGER     NOT NULL,
    successful_alerts INTEGER     NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_alerts_created_at   ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_analysis_id  ON alerts(analysis_id);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id  TEXT        PRIMARY KEY,
    analysis_id  TEXT        NOT NULL,
    action       TEXT        NOT NULL,
    outcome      TEXT        NOT NULL,
    notes        TEXT,
    recorded_at  TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_feedback_analysis_id ON feedback(analysis_id);
CREATE INDEX IF NOT EXISTS idx_feedback_recorded_at ON feedback(recorded_at DESC);
"""


async def _init_connection(conn: asyncpg.Connection) -> None:
    # Registered per-connection so asyncpg transparently encodes/decodes JSONB as dicts.
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def init_pool() -> None:
    global _pool
    log.info("Connecting to database...")
    _pool = await asyncpg.create_pool(
        dsn=DATABASE_URL,
        min_size=2,
        max_size=10,
        init=_init_connection,
    )
    async with _pool.acquire() as conn:
        await conn.execute(_SCHEMA_SQL)
    log.info("Database ready.")


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        log.info("Database pool closed.")


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialised — did startup complete?")
    return _pool
