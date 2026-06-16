"""
POST /feedback  — Operator / user confirms, dismisses, escalates, or overrides an alert.
GET  /feedback  — List recent feedback entries (operator dashboard use).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from models.schemas import FeedbackActionEnum, FeedbackRequest, FeedbackResponse
from services import feedback_service, escalation_service

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback on an analysis",
    description=(
        "Allows a user or operator to confirm (true positive), dismiss (false positive), "
        "escalate, or override an analysis result. Override attempts are rejected once a "
        "conversation has an active fraud-analyst escalation."
    ),
)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    if request.action == FeedbackActionEnum.OVERRIDE and request.session_id:
        if await escalation_service.is_session_locked(request.session_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "This conversation has been escalated to a fraud analyst. "
                    "The user cannot override this case until an analyst resolves it."
                ),
            )

    return await feedback_service.record_feedback(
        analysis_id=request.analysis_id,
        action=request.action,
        session_id=request.session_id,
        notes=request.notes,
    )


@router.get(
    "",
    response_model=list[FeedbackResponse],
    summary="List recent feedback entries",
)
async def list_feedback(
    limit: int = Query(default=50, ge=1, le=200),
) -> list[FeedbackResponse]:
    return await feedback_service.get_recent_feedback(limit=limit)
