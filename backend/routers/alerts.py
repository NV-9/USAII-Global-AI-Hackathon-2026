"""
GET /alerts        — List recent alert broadcasts.
GET /alerts/{id}   — Retrieve a specific alert record.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from models.schemas import AlertListResponse, AlertRecord
from services import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get(
    "",
    response_model=AlertListResponse,
    summary="List recent alert broadcasts",
    description=(
        "Returns the most recent alert records (up to `limit`, default 50). "
        "Each record shows which platforms were alerted and whether each call succeeded."
    ),
)
async def list_alerts(
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of records to return"),
) -> AlertListResponse:
    alerts = await alert_service.get_recent_alerts(limit=limit)
    return AlertListResponse(total=len(alerts), alerts=alerts)


@router.get(
    "/{alert_id}",
    response_model=AlertRecord,
    summary="Retrieve a specific alert record",
)
async def get_alert(alert_id: str) -> AlertRecord:
    record = await alert_service.get_alert_by_id(alert_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found.",
        )
    return record
