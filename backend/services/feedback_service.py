"""Persists operator feedback (confirm / dismiss / escalate) on analysis results."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from db import get_pool
from models.schemas import FeedbackActionEnum, FeedbackResponse


_OUTCOMES = {
    FeedbackActionEnum.CONFIRM: (
        "Alert confirmed as a genuine scam. "
        "The event has been flagged for model training. "
        "Platform blocks remain active until manually released by an operator."
    ),
    FeedbackActionEnum.DISMISS: (
        "Alert dismissed as a false positive. "
        "Platform blocks have been released. "
        "The event is logged to help reduce future false positives."
    ),
    FeedbackActionEnum.ESCALATE: (
        "Case escalated to the human review queue. "
        "A trained operator will assess the evidence and decide on further action. "
        "Payment remains blocked pending human decision."
    ),
    FeedbackActionEnum.OVERRIDE: (
        "User chose to proceed despite the scam warning. "
        "This override has been logged against the conversation and counts toward "
        "automatic escalation to a human fraud analyst if risk continues to climb."
    ),
}


async def record_feedback(
    analysis_id: str,
    action: FeedbackActionEnum,
    session_id: Optional[str] = None,
    notes: Optional[str] = None,
) -> FeedbackResponse:
    feedback_id = str(uuid.uuid4())
    outcome = _OUTCOMES[action]
    recorded_at = datetime.now(timezone.utc)

    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO feedback (feedback_id, analysis_id, session_id, action, outcome, notes, recorded_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            feedback_id,
            analysis_id,
            session_id,
            action.value,
            outcome,
            notes,
            recorded_at,
        )

    return FeedbackResponse(
        feedback_id=feedback_id,
        analysis_id=analysis_id,
        action=action,
        outcome=outcome,
        recorded_at=recorded_at,
    )


async def get_feedback_for_analysis(analysis_id: str) -> List[FeedbackResponse]:
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM feedback WHERE analysis_id = $1 ORDER BY recorded_at DESC",
            analysis_id,
        )
    return [_row_to_feedback(r) for r in rows]


async def get_recent_feedback(limit: int = 50) -> List[FeedbackResponse]:
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM feedback ORDER BY recorded_at DESC LIMIT $1",
            limit,
        )
    return [_row_to_feedback(r) for r in rows]


def _row_to_feedback(row) -> FeedbackResponse:
    return FeedbackResponse(
        feedback_id=row["feedback_id"],
        analysis_id=row["analysis_id"],
        action=FeedbackActionEnum(row["action"]),
        outcome=row["outcome"],
        recorded_at=row["recorded_at"],
    )
