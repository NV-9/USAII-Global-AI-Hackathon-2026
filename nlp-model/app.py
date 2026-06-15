"""FastAPI wrapper around the trained ScamShield NLP model."""

from __future__ import annotations

import pickle
import re
from contextlib import asynccontextmanager
from typing import List

import scipy.sparse as sp
from fastapi import FastAPI
from pydantic import BaseModel


model = None
tfidf = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, tfidf
    with open("scamshield_model.pkl", "rb") as f:
        model = pickle.load(f)
    with open("tfidf_vectorizer.pkl", "rb") as f:
        tfidf = pickle.load(f)
    yield


app = FastAPI(title="ScamShield NLP Service", lifespan=lifespan)


def _count_urgency(text: str) -> int:
    words = ["urgent", "immediately", "now", "hurry", "quick", "fast",
             "limited", "expire", "deadline", "asap", "don't wait",
             "act now", "before it's too late"]
    t = text.lower()
    return sum(1 for w in words if w in t)


def _count_pressure(text: str) -> int:
    phrases = ["trust me", "don't worry", "i also did it", "just ignore",
               "it's fine", "believe me", "i promise", "guaranteed", "no risk"]
    t = text.lower()
    return sum(1 for p in phrases if p in t)


def _count_money(text: str) -> int:
    words = ["send money", "transfer", "bank account", "payment", "crypto",
             "bitcoin", "gift card", "wire", "cash", "invest", "profit",
             "earn", "winning", "prize"]
    t = text.lower()
    return sum(1 for w in words if w in t)


def _count_links(text: str) -> int:
    return len(re.findall(r"https?://[^\s]+", text))


def _count_secrecy(text: str) -> int:
    phrases = ["don't tell", "keep secret", "between us", "don't share",
               "confidential", "private", "don't show", "just you and me"]
    t = text.lower()
    return sum(1 for p in phrases if p in t)


class PredictRequest(BaseModel):
    message: str


class PredictResponse(BaseModel):
    risk_score: int
    risk_level: str
    confidence: float
    triggered_features: List[str]
    requires_human_review: bool


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    msg = req.message
    urgency  = _count_urgency(msg)
    pressure = _count_pressure(msg)
    money    = _count_money(msg)
    links    = _count_links(msg)
    secrecy  = _count_secrecy(msg)

    tfidf_vec = tfidf.transform([msg])
    custom    = [[urgency, pressure, money, links, secrecy, len(msg), len(msg.split())]]
    features  = sp.hstack([tfidf_vec, custom])

    probability = float(model.predict_proba(features)[0][1])
    risk_score  = int(probability * 100)

    if risk_score >= 70:
        risk_level = "HIGH"
    elif risk_score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    triggered: List[str] = []
    if urgency  > 0: triggered.append("urgency")
    if pressure > 0: triggered.append("pressure_tactics")
    if money    > 0: triggered.append("money_request")
    if links    > 0: triggered.append("suspicious_links")
    if secrecy  > 0: triggered.append("secrecy_tactics")
    if not triggered and risk_score >= 40:
        triggered.append("suspicious_language_pattern")

    return PredictResponse(
        risk_score=risk_score,
        risk_level=risk_level,
        confidence=round(probability, 3),
        triggered_features=triggered,
        requires_human_review=risk_level in ("MEDIUM", "HIGH"),
    )


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}
