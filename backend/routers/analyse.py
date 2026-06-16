"""POST /analyse — scores a message for scam risk, triggers a platform alert if HIGH or CRITICAL, and escalates to a fraud analyst if abuse-of-override patterns are detected."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from models.schemas import AnalyseRequest, AnalyseResponse
from services import nlp_service, alert_service, escalation_service
from services.risk_engine import should_broadcast_alert

router = APIRouter(prefix="/analyse", tags=["Analysis"])


@router.post(
    "",
    response_model=AnalyseResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyse a message for scam risk",
    description=(
        "Accepts a conversation message, extracts scam-pattern features via NLP, "
        "returns a risk score (0–100) and risk level, and — for HIGH / CRITICAL "
        "scores — simultaneously broadcasts a block alert to all registered payment "
        "platforms.  The message text is never stored."
    ),
)
async def analyse(request: AnalyseRequest) -> AnalyseResponse:
    result = await nlp_service.analyse_message(
        message=request.message,
        session_id=request.session_id,
        platform_context=request.platform_context,
    )

    alert_triggered = False
    alert_id = None

    if should_broadcast_alert(result["risk_level"]):
        alert_record = await alert_service.broadcast_alert(
            analysis_id=result["analysis_id"],
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            session_id=request.session_id,
            simulate=True,  # set False in production with real webhook URLs
        )
        alert_triggered = True
        alert_id = alert_record.alert_id

    escalation_triggered = False
    escalation_id = None
    override_locked = False

    if request.session_id:
        if await escalation_service.should_escalate(request.session_id, result["risk_score"]):
            escalation = await escalation_service.create_escalation(
                session_id=request.session_id,
                analysis_id=result["analysis_id"],
                risk_score=result["risk_score"],
            )
            escalation_triggered = True
            escalation_id = escalation.escalation_id

        override_locked = await escalation_service.is_session_locked(request.session_id)

    return AnalyseResponse(
        **result,
        alert_triggered=alert_triggered,
        alert_id=alert_id,
        escalation_triggered=escalation_triggered,
        escalation_id=escalation_id,
        override_locked=override_locked,
    )
