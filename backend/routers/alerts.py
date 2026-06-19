"""
GET /alerts        — List recent alert broadcasts.
GET /alerts/{id}   — Retrieve a specific alert record.
"""

from __future__ import annotations

import math
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from models.schemas import AlertListResponse, AlertRecord
from services import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get(
    "",
    response_model=AlertListResponse,
    summary="List recent alert broadcasts",
    description=(
        "Returns a page of recent alert records, most recent first. "
        "Each record shows which platforms were alerted and whether each call succeeded."
    ),
)
async def list_alerts(
    page: int = Query(default=1, ge=1, description="1-indexed page number"),
    page_size: int = Query(default=10, ge=1, le=200, description="Number of records per page"),
    limit: Optional[int] = Query(
        default=None, ge=1, le=200,
        description="Legacy parameter, equivalent to page_size with page=1.",
    ),
) -> AlertListResponse:
    if limit is not None:
        page_size = limit
        page = 1

    total = await alert_service.count_alerts()
    offset = (page - 1) * page_size
    alerts = await alert_service.get_recent_alerts(limit=page_size, offset=offset)
    total_pages = max(1, math.ceil(total / page_size))

    return AlertListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        alerts=alerts,
    )


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
