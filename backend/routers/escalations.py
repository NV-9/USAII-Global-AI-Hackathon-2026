"""
GET  /escalations             — List escalations for the analyst dashboard (pending by default).
GET  /escalations/{id}        — Retrieve a specific escalation.
POST /escalations/{id}/resolve — Analyst resolves an escalation, unlocking the conversation.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from models.schemas import EscalationListResponse, EscalationRecord, EscalationResolveRequest
from services import escalation_service

router = APIRouter(prefix="/escalations", tags=["Escalations"])


@router.get(
    "",
    response_model=EscalationListResponse,
    summary="List fraud-analyst escalations",
    description="Returns pending escalations by default. Pass pending_only=false to see resolved cases too.",
)
async def list_escalations(
    pending_only: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=200),
) -> EscalationListResponse:
    escalations = (
        await escalation_service.get_pending_escalations(limit=limit)
        if pending_only
        else await escalation_service.get_recent_escalations(limit=limit)
    )
    return EscalationListResponse(total=len(escalations), escalations=escalations)


@router.get(
    "/{escalation_id}",
    response_model=EscalationRecord,
    summary="Retrieve a specific escalation",
)
async def get_escalation(escalation_id: str) -> EscalationRecord:
    record = await escalation_service.get_escalation_by_id(escalation_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Escalation '{escalation_id}' not found.")
    return record


@router.post(
    "/{escalation_id}/resolve",
    response_model=EscalationRecord,
    summary="Resolve an escalation",
    description="A human analyst confirms fraud (block stays permanent) or releases the conversation, unlocking overrides.",
)
async def resolve_escalation(escalation_id: str, request: EscalationResolveRequest) -> EscalationRecord:
    record = await escalation_service.resolve_escalation(
        escalation_id=escalation_id,
        resolution=request.resolution,
        notes=request.notes,
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Escalation '{escalation_id}' not found.")
    return record
