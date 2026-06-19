"""Central configuration: risk thresholds, webhook URLs, NLP weights, and database settings."""

import os
from typing import Dict


class RiskLevel:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


RISK_THRESHOLDS = {
    RiskLevel.LOW: (0, 39),
    RiskLevel.MEDIUM: (40, 69),
    RiskLevel.HIGH: (70, 89),
    RiskLevel.CRITICAL: (90, 100),
}

HUMAN_REVIEW_THRESHOLD = 70
MIN_CONFIDENCE_FOR_AUTO_ACTION = 0.60

FRAUD_ANALYST_RISK_THRESHOLD = 90
FRAUD_ANALYST_MIN_OVERRIDES = 1
FRAUD_ANALYST_MIN_FLAGGED_MESSAGES = 2

PLATFORM_WEBHOOKS: Dict[str, str] = {
    "paypal":   "http://localhost:9001/webhook/paypal",
    "venmo":    "http://localhost:9001/webhook/venmo",
    "cashapp":  "http://localhost:9001/webhook/cashapp",
    "revolut":  "http://localhost:9001/webhook/revolut",
    "zelle":    "http://localhost:9001/webhook/zelle",
    "wise":     "http://localhost:9001/webhook/wise",
}

WEBHOOK_TIMEOUT_SECONDS = 5
ALERT_BROADCAST_TIMEOUT = 8

NLP_FEATURE_WEIGHTS = {
    "urgency_keywords":       20,
    "pressure_phrases":       18,
    "impersonation_markers":  15,
    "money_request_patterns": 20,
    "secrecy_phrases":        12,
    "emotional_manipulation": 10,
    "style_anomaly":           5,
}

MAX_RAW_SCORE = sum(NLP_FEATURE_WEIGHTS.values())

APP_TITLE = "ThinkAgainAI Backend API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = (
    "Receives messages, runs NLP scam detection, returns a risk score, "
    "and triggers simulated cross-platform payment alerts."
)

DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql://scamshield:scamshield@localhost:5432/scamshield",
)

NLP_SERVICE_URL: str = os.environ.get("NLP_SERVICE_URL", "http://localhost:8001")
