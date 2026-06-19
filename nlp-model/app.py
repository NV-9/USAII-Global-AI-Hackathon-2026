"""FastAPI wrapper around the fine-tuned ScamShield BERT model."""

from __future__ import annotations

import re
from contextlib import asynccontextmanager
from typing import List

import torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_DIR = "scamshield_bert_model"
MAX_LENGTH = 256

tokenizer = None
model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global tokenizer, model
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    model.eval()
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

    inputs = tokenizer(
        msg,
        return_tensors="pt",
        truncation=True,
        max_length=MAX_LENGTH,
        padding=True,
    )
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)[0]  # [P(low), P(medium), P(high)]
    p_low, p_medium, p_high = (float(p) for p in probs)

    predicted_idx = int(torch.argmax(probs))
    risk_level = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}[predicted_idx]
    probability = float(probs[predicted_idx])
    risk_score = round(p_medium * 50 + p_high * 100)

    urgency  = _count_urgency(msg)
    pressure = _count_pressure(msg)
    money    = _count_money(msg)
    links    = _count_links(msg)
    secrecy  = _count_secrecy(msg)

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
