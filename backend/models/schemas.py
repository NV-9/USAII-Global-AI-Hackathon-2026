from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class RiskLevelEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatusEnum(str, Enum):
    SENT = "SENT"
    FAILED = "FAILED"
    SIMULATED = "SIMULATED"


class FeedbackActionEnum(str, Enum):
    CONFIRM = "confirm"       # user agrees it is a scam
    DISMISS = "dismiss"       # user says it is a false positive
    ESCALATE = "escalate"     # user wants human review


class AnalyseRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description="The conversation message to analyse. Never stored after scoring.",
        examples=["Hey it's me, I'm in trouble and need you to send £500 urgently. Don't tell anyone."],
    )
    platform_context: Optional[str] = Field(
        None,
        description="Optional platform hint (e.g. 'instagram', 'whatsapp') for context weighting.",
        examples=["instagram"],
    )
    session_id: Optional[str] = Field(
        None,
        description="Caller-supplied session ID for correlating analysis with feedback.",
    )


class NLPFeatureScores(BaseModel):
    urgency_keywords: int = Field(ge=0)
    pressure_phrases: int = Field(ge=0)
    impersonation_markers: int = Field(ge=0)
    money_request_patterns: int = Field(ge=0)
    secrecy_phrases: int = Field(ge=0)
    emotional_manipulation: int = Field(ge=0)
    style_anomaly: int = Field(ge=0)


class AnalyseResponse(BaseModel):
    analysis_id: str = Field(description="Unique ID for this analysis event.")
    session_id: Optional[str] = None
    risk_score: int = Field(ge=0, le=100, description="Composite scam risk score (0–100).")
    risk_level: RiskLevelEnum
    confidence: float = Field(ge=0.0, le=1.0, description="Model confidence in the classification.")
    feature_scores: NLPFeatureScores
    triggered_features: List[str] = Field(description="Human-readable list of detected signals.")
    recommended_action: str = Field(description="Suggested action for the operator or platform.")
    requires_human_review: bool
    alert_triggered: bool
    alert_id: Optional[str] = Field(None, description="ID of the alert broadcast if one was fired.")
    analysed_at: datetime


class PlatformAlertResult(BaseModel):
    platform: str
    status: AlertStatusEnum
    http_status: Optional[int] = None
    error: Optional[str] = None
    sent_at: datetime


class AlertRecord(BaseModel):
    alert_id: str
    analysis_id: str
    risk_score: int
    risk_level: RiskLevelEnum
    platform_results: List[PlatformAlertResult]
    total_platforms: int
    successful_alerts: int
    created_at: datetime


class AlertListResponse(BaseModel):
    total: int
    alerts: List[AlertRecord]

class FeedbackRequest(BaseModel):
    analysis_id: str = Field(description="ID returned by /analyse.")
    action: FeedbackActionEnum
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional operator notes (e.g. why they are dismissing the alert).",
    )

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v


class FeedbackResponse(BaseModel):
    feedback_id: str
    analysis_id: str
    action: FeedbackActionEnum
    outcome: str = Field(description="What the system did in response to this feedback.")
    recorded_at: datetime

class HealthResponse(BaseModel):
    status: str
    version: str
    nlp_backend: str
    platform_count: int
    uptime_seconds: float
