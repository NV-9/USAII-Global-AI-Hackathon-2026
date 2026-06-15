"""
POST /feedback  — Operator / user confirms or dismisses an alert.
GET  /feedback  — List recent feedback entries (operator dashboard use).
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from models.schemas import FeedbackRequest, FeedbackResponse
from services import feedback_service

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback on an analysis",
    description=(
        "Allows a user or operator to confirm (true positive), dismiss (false positive), "
        "or escalate an analysis result.  Feedback is used to close the human-in-the-loop "
        "cycle and improve model accuracy over time."
    ),
)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    return await feedback_service.record_feedback(
        analysis_id=request.analysis_id,
        action=request.action,
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
