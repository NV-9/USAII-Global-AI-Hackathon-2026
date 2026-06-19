"""Triggers and tracks fraud-analyst escalations for high-risk conversations the user has already tried to override."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from config import (
    FRAUD_ANALYST_RISK_THRESHOLD,
    FRAUD_ANALYST_MIN_OVERRIDES,
    FRAUD_ANALYST_MIN_FLAGGED_MESSAGES,
)
from db import get_pool
from models.schemas import (
    EscalationRecord,
    EscalationResolutionEnum,
    EscalationStatusEnum,
)


async def count_flagged_messages(session_id: str) -> int:
    pool = get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT COUNT(*) FROM alerts WHERE session_id = $1",
            session_id,
        )


async def count_overrides(session_id: str) -> int:
    pool = get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT COUNT(*) FROM feedback WHERE session_id = $1 AND action = 'override'",
            session_id,
        )


async def is_session_locked(session_id: str) -> bool:
    pool = get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM escalations WHERE session_id = $1 AND status = $2",
            session_id,
            EscalationStatusEnum.PENDING.value,
        )
    return count > 0


async def should_escalate(session_id: Optional[str], risk_score: int) -> bool:
    if not session_id or risk_score <= FRAUD_ANALYST_RISK_THRESHOLD:
        return False
    overrides = await count_overrides(session_id)
    flagged = await count_flagged_messages(session_id)
    return (
        overrides >= FRAUD_ANALYST_MIN_OVERRIDES
        and flagged >= FRAUD_ANALYST_MIN_FLAGGED_MESSAGES
    )


async def create_escalation(session_id: str, analysis_id: str, risk_score: int) -> EscalationRecord:
    escalation_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)
    reason = (
        f"Risk score {risk_score} exceeded {FRAUD_ANALYST_RISK_THRESHOLD}, the user has already "
        f"attempted to override at least once, and multiple messages in this conversation have "
        f"been flagged. Escalated to a human fraud analyst; transaction is hard-blocked."
    )

    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO escalations
                (escalation_id, session_id, analysis_id, risk_score, reason, status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            escalation_id,
            session_id,
            analysis_id,
            risk_score,
            reason,
            EscalationStatusEnum.PENDING.value,
            created_at,
        )

    return EscalationRecord(
        escalation_id=escalation_id,
        session_id=session_id,
        analysis_id=analysis_id,
        risk_score=risk_score,
        reason=reason,
        status=EscalationStatusEnum.PENDING,
        created_at=created_at,
    )


async def resolve_escalation(
    escalation_id: str,
    resolution: EscalationResolutionEnum,
    notes: Optional[str] = None,
) -> Optional[EscalationRecord]:
    resolved_at = datetime.now(timezone.utc)
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE escalations
            SET status = $1, resolution = $2, resolution_notes = $3, resolved_at = $4
            WHERE escalation_id = $5
            RETURNING *
            """,
            EscalationStatusEnum.RESOLVED.value,
            resolution.value,
            notes,
            resolved_at,
            escalation_id,
        )
    return _row_to_escalation(row) if row else None


async def get_pending_escalations(limit: int = 50) -> List[EscalationRecord]:
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM escalations WHERE status = $1 ORDER BY created_at DESC LIMIT $2",
            EscalationStatusEnum.PENDING.value,
            limit,
        )
    return [_row_to_escalation(r) for r in rows]


async def get_recent_escalations(limit: int = 50) -> List[EscalationRecord]:
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM escalations ORDER BY created_at DESC LIMIT $1",
            limit,
        )
    return [_row_to_escalation(r) for r in rows]


async def get_escalation_by_id(escalation_id: str) -> Optional[EscalationRecord]:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM escalations WHERE escalation_id = $1",
            escalation_id,
        )
    return _row_to_escalation(row) if row else None


def _row_to_escalation(row) -> EscalationRecord:
    return EscalationRecord(
        escalation_id=row["escalation_id"],
        session_id=row["session_id"],
        analysis_id=row["analysis_id"],
        risk_score=row["risk_score"],
        reason=row["reason"],
        status=EscalationStatusEnum(row["status"]),
        resolution=EscalationResolutionEnum(row["resolution"]) if row["resolution"] else None,
        resolution_notes=row["resolution_notes"],
        created_at=row["created_at"],
        resolved_at=row["resolved_at"],
    )
