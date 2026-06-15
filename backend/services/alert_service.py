"""Fans out scam alerts to all registered payment platforms in parallel and persists the results."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import httpx

from config import (
    PLATFORM_WEBHOOKS,
    WEBHOOK_TIMEOUT_SECONDS,
    ALERT_BROADCAST_TIMEOUT,
)
from db import get_pool
from models.schemas import AlertRecord, AlertStatusEnum, PlatformAlertResult, RiskLevelEnum


def _build_payload(
    alert_id: str,
    analysis_id: str,
    risk_score: int,
    risk_level: str,
    platform: str,
    sent_at: datetime,
) -> dict:
    return {
        "event": "SCAM_ALERT",
        "alert_id": alert_id,
        "analysis_id": analysis_id,
        "platform": platform,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "action_requested": "BLOCK_OUTBOUND_TRANSFERS",
        "sent_at": sent_at.isoformat(),
        "ttl_seconds": 300,
    }


async def _dispatch_to_platform(
    client: httpx.AsyncClient,
    platform: str,
    url: str,
    payload: dict,
    sent_at: datetime,
    simulate: bool,
) -> PlatformAlertResult:
    if simulate:
        return PlatformAlertResult(
            platform=platform,
            status=AlertStatusEnum.SIMULATED,
            http_status=200,
            sent_at=sent_at,
        )

    try:
        response = await client.post(url, json=payload, timeout=WEBHOOK_TIMEOUT_SECONDS)
        return PlatformAlertResult(
            platform=platform,
            status=AlertStatusEnum.SENT if response.is_success else AlertStatusEnum.FAILED,
            http_status=response.status_code,
            sent_at=sent_at,
        )
    except httpx.TimeoutException:
        return PlatformAlertResult(
            platform=platform,
            status=AlertStatusEnum.FAILED,
            error="Timeout",
            sent_at=sent_at,
        )
    except Exception as exc:  # noqa: BLE001
        return PlatformAlertResult(
            platform=platform,
            status=AlertStatusEnum.FAILED,
            error=str(exc),
            sent_at=sent_at,
        )


async def broadcast_alert(
    analysis_id: str,
    risk_score: int,
    risk_level: str,
    simulate: bool = True,
) -> AlertRecord:
    alert_id = str(uuid.uuid4())
    sent_at = datetime.now(timezone.utc)

    payloads = {
        platform: _build_payload(alert_id, analysis_id, risk_score, risk_level, platform, sent_at)
        for platform, url in PLATFORM_WEBHOOKS.items()
    }

    async with httpx.AsyncClient() as client:
        tasks = [
            _dispatch_to_platform(client, platform, url, payloads[platform], sent_at, simulate)
            for platform, url in PLATFORM_WEBHOOKS.items()
        ]
        try:
            results: List[PlatformAlertResult] = await asyncio.wait_for(
                asyncio.gather(*tasks),
                timeout=ALERT_BROADCAST_TIMEOUT,
            )
        except asyncio.TimeoutError:
            results = [
                PlatformAlertResult(
                    platform=p,
                    status=AlertStatusEnum.FAILED,
                    error="Global broadcast timeout",
                    sent_at=sent_at,
                )
                for p in PLATFORM_WEBHOOKS
            ]

    successful = sum(
        1 for r in results
        if r.status in (AlertStatusEnum.SENT, AlertStatusEnum.SIMULATED)
    )

    record = AlertRecord(
        alert_id=alert_id,
        analysis_id=analysis_id,
        risk_score=risk_score,
        risk_level=RiskLevelEnum(risk_level),
        platform_results=list(results),
        total_platforms=len(PLATFORM_WEBHOOKS),
        successful_alerts=successful,
        created_at=sent_at,
    )

    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO alerts
                (alert_id, analysis_id, risk_score, risk_level,
                 platform_results, total_platforms, successful_alerts, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            record.alert_id,
            record.analysis_id,
            record.risk_score,
            record.risk_level.value,
            [r.model_dump(mode="json") for r in record.platform_results],
            record.total_platforms,
            record.successful_alerts,
            record.created_at,
        )

    return record


async def get_recent_alerts(limit: int = 50) -> List[AlertRecord]:
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM alerts ORDER BY created_at DESC LIMIT $1",
            limit,
        )
    return [_row_to_alert(r) for r in rows]


async def get_alert_by_id(alert_id: str) -> Optional[AlertRecord]:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM alerts WHERE alert_id = $1",
            alert_id,
        )
    return _row_to_alert(row) if row else None


def _row_to_alert(row) -> AlertRecord:
    platform_results = [
        PlatformAlertResult(**r) for r in row["platform_results"]
    ]
    return AlertRecord(
        alert_id=row["alert_id"],
        analysis_id=row["analysis_id"],
        risk_score=row["risk_score"],
        risk_level=RiskLevelEnum(row["risk_level"]),
        platform_results=platform_results,
        total_platforms=row["total_platforms"],
        successful_alerts=row["successful_alerts"],
        created_at=row["created_at"],
    )
