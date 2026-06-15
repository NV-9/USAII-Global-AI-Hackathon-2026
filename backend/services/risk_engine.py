"""Maps a 0–100 risk score to a risk level and recommended operator action."""

from __future__ import annotations

from config import RISK_THRESHOLDS, RiskLevel, MIN_CONFIDENCE_FOR_AUTO_ACTION


_ACTIONS: dict[str, str] = {
    RiskLevel.LOW: (
        "No action required. Monitor for further signals. "
        "Payment may proceed normally."
    ),
    RiskLevel.MEDIUM: (
        "Display an in-app scam warning to the sender. "
        "Require explicit user confirmation before completing the transfer. "
        "Log event for review."
    ),
    RiskLevel.HIGH: (
        "Block the payment immediately. "
        "Broadcast alert to all registered payment platforms to prevent switching. "
        "Notify the user with guidance on how to verify the recipient's identity."
    ),
    RiskLevel.CRITICAL: (
        "Hard-block all payment channels. "
        "Escalate to human review queue immediately. "
        "Provide the user with a crisis support link. "
        "A human operator must authorise any unblock."
    ),
}


def score_to_risk_level(score: int) -> str:
    for level, (low, high) in RISK_THRESHOLDS.items():
        if low <= score <= high:
            return level
    return RiskLevel.CRITICAL  # safety fallback for scores above 100


def recommended_action(risk_level: str, confidence: float) -> str:
    base = _ACTIONS.get(risk_level, _ACTIONS[RiskLevel.LOW])

    if confidence < MIN_CONFIDENCE_FOR_AUTO_ACTION:
        base += (
            f" NOTE: Model confidence is low ({confidence:.0%}). "
            "Human review is strongly recommended before taking action."
        )

    return base


def should_broadcast_alert(risk_level: str) -> bool:
    return risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
