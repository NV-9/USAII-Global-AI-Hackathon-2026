"""Calls the NLP model service for scam scoring, with a rule-based fallback if it is unreachable."""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx

from config import NLP_FEATURE_WEIGHTS, MAX_RAW_SCORE, MIN_CONFIDENCE_FOR_AUTO_ACTION, NLP_SERVICE_URL
from models.schemas import NLPFeatureScores

log = logging.getLogger(__name__)

_FEATURE_LABEL_MAP = {
    "urgency":                    "Urgency language detected",
    "pressure_tactics":           "Pressure / coercion phrases detected",
    "money_request":              "Money transfer request detected",
    "suspicious_links":           "Suspicious links detected",
    "secrecy_tactics":            "Secrecy / isolation tactics detected",
    "suspicious_language_pattern":"Suspicious language pattern (model detection)",
}

_MODEL_FEATURE_TO_SCORE_FIELD = {
    "urgency":        "urgency_keywords",
    "pressure_tactics": "pressure_phrases",
    "money_request":  "money_request_patterns",
    "suspicious_links": "style_anomaly",
    "secrecy_tactics": "secrecy_phrases",
}


async def analyse_message(
    message: str,
    session_id: Optional[str] = None,
    platform_context: Optional[str] = None,
) -> dict:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(f"{NLP_SERVICE_URL}/predict", json={"message": message})
            resp.raise_for_status()
            return _build_result_from_model(resp.json(), message, session_id)
    except Exception as exc:
        log.warning("NLP service unavailable (%s) — using rule-based fallback.", exc)
        return _rule_based_result(message, session_id)


def _build_result_from_model(payload: dict, message: str, session_id: Optional[str]) -> dict:
    from services.risk_engine import recommended_action
    from config import HUMAN_REVIEW_THRESHOLD

    risk_score  = payload["risk_score"]
    risk_level  = payload["risk_level"]
    confidence  = payload["confidence"]
    triggered   = payload["triggered_features"]

    scores_dict = {k: 0 for k in NLPFeatureScores.model_fields}
    for feature in triggered:
        field = _MODEL_FEATURE_TO_SCORE_FIELD.get(feature)
        if field:
            scores_dict[field] = NLP_FEATURE_WEIGHTS.get(field, 0)

    feature_scores = NLPFeatureScores(**scores_dict)
    human_labels   = [_FEATURE_LABEL_MAP[f] for f in triggered if f in _FEATURE_LABEL_MAP]

    # Model confidence is the scam probability; certainty of classification
    # is how far it sits from the 0.5 decision boundary.
    # A score of 0.015 means 98.5% sure it is legitimate — that is certain, not uncertain.
    certainty = abs(confidence - 0.5) * 2
    requires_human_review = (
        risk_score >= HUMAN_REVIEW_THRESHOLD
        or (certainty < MIN_CONFIDENCE_FOR_AUTO_ACTION and risk_score > 20)
    )

    return {
        "analysis_id":        str(uuid.uuid4()),
        "session_id":         session_id,
        "risk_score":         risk_score,
        "risk_level":         risk_level,
        "confidence":         confidence,
        "feature_scores":     feature_scores,
        "triggered_features": human_labels,
        "recommended_action": recommended_action(risk_level, confidence),
        "requires_human_review": requires_human_review,
        "analysed_at":        datetime.now(timezone.utc),
    }


_URGENCY = re.compile(
    r"\b(urgent|urgently|immediately|right now|asap|emergency|hurry|quick|"
    r"don'?t wait|time.sensitive|last chance|act now|expires?(?: today| soon)?|"
    r"limited time|deadline|critical|crisis|straight away|this instant)\b",
    re.IGNORECASE,
)
_PRESSURE = re.compile(
    r"\b(you must|you have to|you need to|i need you to|please please|"
    r"i'?m begging|i'?m desperate|trust me|just this once|no choice|"
    r"or else|if you don'?t|won'?t forgive|let me down|counting on you|"
    r"need you to send|need you to transfer|have to do this)\b",
    re.IGNORECASE,
)
_IMPERSONATION = re.compile(
    r"\b(it'?s me|its me|this is me|it is me|"
    r"it'?s (?:your )?(?:mum|mom|dad|brother|sister|friend|son|daughter|gran|grandma|grandpa)|"
    r"new (?:number|phone)|lost my (?:phone|sim)|"
    r"hacked|changed (?:my )?number|different (?:phone|device|number)|"
    r"new device|messaging from|writing from a)\b",
    re.IGNORECASE,
)
_MONEY_REQUEST = re.compile(
    r"\b(send money|bank transfer|wire transfer|wire me|paypal|venmo|cashapp|"
    r"cash app|zelle|revolut|wise|monzo|crypto|bitcoin|ethereum|gift card|"
    r"voucher code|pay me|lend me|borrow|loan me|"
    r"send (?:me |us )?(?:some |a )?(?:cash|money|funds)|"
    r"i need (?:cash|money|funds)|transfer (?:the )?(?:cash|money|funds)|"
    r"send (?:\d+|a few|some|the)|need (?:\d+|a few hundred|some money)|"
    r"[\$£€]\s*\d+|\d+\s*(?:dollars|pounds|euros|gbp|usd|eur))\b",
    re.IGNORECASE,
)
_SECRECY = re.compile(
    r"\b(don'?t tell|dont tell|keep this (?:between us|secret|quiet|private)|"
    r"no one (?:else |must |should )?know|just (?:between us|you and me)|"
    r"don'?t mention|don'?t say anything|nobody (?:else )?needs to know|"
    r"keep it quiet|our secret|between you and me)\b",
    re.IGNORECASE,
)
_EMOTIONAL = re.compile(
    r"\b(i'?m (?:scared|terrified|in danger|hurt|trapped|stuck|stranded|crying|desperate)|"
    r"please help(?: me)?|i don'?t know what to do|"
    r"you'?re (?:my only|the only one)|i have no one|"
    r"scared for (?:my )?life|love you so much|means everything|"
    r"really need you|i'?m in trouble)\b",
    re.IGNORECASE,
)
_CAPS_WORDS  = re.compile(r"\b[A-Z]{4,}\b")
_EXCESS_PUNCT = re.compile(r"[!?]{2,}")


def _rule_based_result(message: str, session_id: Optional[str]) -> dict:
    from services.risk_engine import score_to_risk_level, recommended_action
    from config import HUMAN_REVIEW_THRESHOLD

    def _score(pattern, key):
        return NLP_FEATURE_WEIGHTS[key] if pattern.search(message) else 0

    caps_hits  = len(_CAPS_WORDS.findall(message))
    punct_hits = len(_EXCESS_PUNCT.findall(message))

    feature_scores = NLPFeatureScores(
        urgency_keywords=      _score(_URGENCY,       "urgency_keywords"),
        pressure_phrases=      _score(_PRESSURE,      "pressure_phrases"),
        impersonation_markers= _score(_IMPERSONATION, "impersonation_markers"),
        money_request_patterns=_score(_MONEY_REQUEST, "money_request_patterns"),
        secrecy_phrases=       _score(_SECRECY,       "secrecy_phrases"),
        emotional_manipulation=_score(_EMOTIONAL,     "emotional_manipulation"),
        style_anomaly=NLP_FEATURE_WEIGHTS["style_anomaly"] if (caps_hits + punct_hits) >= 2 else 0,
    )

    raw_score  = sum(feature_scores.model_dump().values())
    risk_score = min(int((raw_score / MAX_RAW_SCORE) * 100), 100)

    active       = [k for k, v in feature_scores.model_dump().items() if v > 0]
    breadth      = min(len(active) / 7, 1.0) * 0.4
    confidence   = round(min(breadth + (raw_score / MAX_RAW_SCORE) * 0.6, 1.0), 3)
    risk_level   = score_to_risk_level(risk_score)

    descriptions = {
        "urgency_keywords":       "Urgency language detected",
        "pressure_phrases":       "Pressure / coercion phrases detected",
        "impersonation_markers":  "Possible impersonation markers",
        "money_request_patterns": "Money transfer request detected",
        "secrecy_phrases":        "Secrecy / isolation tactics detected",
        "emotional_manipulation": "Emotional manipulation language",
        "style_anomaly":          "Unusual writing style (caps / excessive punctuation)",
    }

    return {
        "analysis_id":        str(uuid.uuid4()),
        "session_id":         session_id,
        "risk_score":         risk_score,
        "risk_level":         risk_level,
        "confidence":         confidence,
        "feature_scores":     feature_scores,
        "triggered_features": [descriptions[k] for k in active],
        "recommended_action": recommended_action(risk_level, confidence),
        "requires_human_review": (
            risk_score >= HUMAN_REVIEW_THRESHOLD
            or (confidence < MIN_CONFIDENCE_FOR_AUTO_ACTION and risk_score > 20)
        ),
        "analysed_at": datetime.now(timezone.utc),
    }
