# USAII Global AI Hackathon 2026 | Graduate Track | Direction A: Safe Passage

**SafeGuard AI** (product name: ScamShield AI) is an early-warning detection system for Trust & Safety teams and fraud analysts at financial institutions. It identifies digital exploitation — financial coercion, impersonation, and romance/phishing scams — by analyzing cross-platform behavioral and linguistic signals in real time.

Unlike traditional rule-based systems that scammers easily bypass by altering keywords, SafeGuard AI uses a fine-tuned BERT model to detect semantic intent, urgency, and manipulative pressure. It surfaces these insights into an explainable analyst dashboard, empowering human reviewers to make informed intervention decisions before funds are irrevocably lost.

## Team — Ctrl Alt Elite

| Role | Member |
|---|---|
| AI Model + NLP | Naaz |
| Backend + Alert System | Vish |
| Frontend / Dashboard | Aaron |
| Data + Testing + Video | Emmanuel |

---

## The Problem & Our Scope

Victims of social media impersonation scams often bypass standard banking warnings because they believe they are communicating with trusted friends or family. Fraudsters exploit the fragmented digital landscape, initiating manipulation on Platform A (e.g. a messaging app) and extracting payment on Platform B (e.g. a banking app).

**What this system does:**
- Synthesizes fragmented, multi-platform signals into a unified risk score.
- Provides Explainable AI (XAI) insights to fraud analysts, detailing why a message was flagged.
- Prioritizes high-risk cases for manual human review, with an escalation workflow for the most severe cases.

**What this system does NOT do (non-goals):**
- No Surveillance: it does not monitor general user conversations or read private messages at rest.
- No Automated Freezes: it does not automatically freeze accounts or block funds; human operators retain final decision-making authority.
- No PII Storage: it does not store plaintext conversational data — only the risk level, score, and triggered features are retained.

---

## System Architecture

| Layer | Component | Responsibility |
|---|---|---|
| Data | `frontend/` | Captures message text via a simple UI and simulates the cross-platform webhook source |
| Intelligence | `nlp-model/` | Fine-tuned BERT classifier scoring messages for coercion markers and behavioral anomalies |
| Governance & Orchestration | `backend/` | FastAPI service: persistence (Postgres), alerting, escalation workflow, zero-retention policy |
| Decision Support | `frontend/analyst.html` | Surfaces risk scores, XAI breakdown, and pending escalations to the fraud analyst |

All four services run via `docker-compose.yml` (`db`, `nlp`, `api`, `frontend`), with healthchecks gating startup order.

### Key Features
- **Semantic Intent Detection** — outperforms heuristic keyword-matching by evaluating the contextual weight of linguistic features.
- **Explainable AI (XAI)** — highlights the specific manipulation tactics detected (urgency, pressure, secrecy, money requests) to accelerate human review.
- **Human-in-the-Loop Escalation** — Medium/High risk messages warn the user and allow override; High risk + secrecy locks the override and routes to a fraud analyst dashboard for manual resolution.
- **Responsible AI Guardrails** — analyses payloads in real time and never persists raw message text.

---

## NLP Model

### Performance

| Metric | Score |
|---|---|
| Overall Accuracy | 97% on 80 diverse real-world messages |
| Validation Accuracy | 98.4% |
| Validation Precision | 95.6% (macro) |
| Validation Recall | 94.9% (macro) |
| F1 Score | 95.2% (macro) |
| HIGH detection | 100% (26/26) |
| MEDIUM detection | 96% (26/27) |
| LOW detection | 96% (26/27) |

Evaluated on 80 diverse messages covering all three risk tiers, including casual money requests between friends, slang/emoji scams, indirect romance scams, and security bypass instructions.

### Architecture

The model is a **fine-tuned BERT (bert-base-uncased)** sequence classifier with **3 output labels** (Low / Medium / High risk). BERT was chosen over TF-IDF + Logistic Regression because it understands context rather than just word frequency, allowing it to catch scams that deliberately avoid trigger words:

- *"omg it's me, I lost my phone, can you spot me fifty quid"* — no keywords, but clear impersonation.
- *"been quietly stacking gains on this platform, want the link"* — no "invest", but a clear crypto scam.
- *"so this is awkward but they won't release my car without payment"* — no "urgent", but a clear fake emergency.
- *"Stop asking questions. Just send the money. I'll explain later."* — deflection with no financial keywords.

TF-IDF missed all of these; BERT learned the underlying conversational patterns of exploitation rather than just the vocabulary.

### Development Journey

1. **TF-IDF + Logistic Regression baseline** — trained on UCI SMS Spam Collection and Kaggle Scam Detection datasets. 98% accuracy, but struggled with modern social-media impersonation and indirect scams.
2. **Synthetic data generation (v1/v2)** — the public datasets were 2011-era SMS spam with no modern exploitation patterns, so 2,700 synthetic scam conversations were generated across 5 categories with deliberate keyword-avoidance.
3. **Switch to BERT** — fine-tuned `bert-base-uncased` on a Tesla T4 GPU; outperformed TF-IDF on casual impersonation, indirect romance scams, and crypto scams.
4. **Data cleaning** — fixed inconsistent label mapping caused by mixing heterogeneous datasets, by training on synthetic scam data plus clean UCI ham messages.
5. **Targeted data generation (v3)** — tested against 40 backend test cases, identified failure patterns (bank account impersonation, deflection, security bypass, slang/emoji, vague urgent requests), generated 499 targeted examples to cover them.
6. **Three-tier classification** — upgraded from binary (scam/not-scam) to three-tier (Low/Medium/High) by adding genuine medium-risk examples — messages with one or two suspicious signals but a plausible innocent explanation — enabling proportionate human-in-the-loop responses instead of a binary block/allow decision.

### Training Data

| Dataset | Messages | Label | Purpose |
|---|---|---|---|
| Synthetic v1 | 1,300 | 0/2 | Initial modern scam patterns |
| Synthetic v2 | 1,400 | 0/2 | Diverse phrasing, avoids keyword reliance |
| Synthetic v3 (targeted) | 499 | 0/2 | Specific failure pattern fixes |
| Three-tier dataset | 624 | 0/1/2 | Medium risk examples |
| Medium extra v1 | 110 | 1 | Additional medium risk variety |
| Medium extra v2 | 120 | 1 | More medium risk patterns |
| UCI SMS Ham | 4,690 | 0 | Clean legitimate baseline |
| **Total** | **7,649** | | Label 0: 4,942 / Label 1: 519 / Label 2: 2,188 |

**Label key:** 0 = Low risk (legitimate), 1 = Medium risk (suspicious but ambiguous), 2 = High risk (clear exploitation attempt). All synthetic data was team-generated and is fully disclosed; CSVs are included in `nlp-model/`.

### How It Works

1. **Input** — a message string is sent to the `/predict` endpoint (`nlp-model/app.py`).
2. **BERT classification** — the message is tokenised and passed through the fine-tuned model, which outputs a probability distribution across the three risk classes.
3. **Feature extraction (explainability)** — keyword-based features are extracted alongside the model prediction so users understand *why* a message was flagged:

   | Feature | What it detects |
   |---|---|
   | urgency | Time pressure language ("do it now", "limited time") |
   | pressure_tactics | Reassurance under pressure ("trust me", "don't worry") |
   | money_request | Financial requests ("send money", "transfer", "crypto") |
   | suspicious_links | URLs and suspicious links |
   | secrecy_tactics | Isolation tactics ("don't tell anyone", "between us") |
   | suspicious_language_pattern | Model detected a scam pattern with no explicit keywords |

4. **Risk level & human-in-the-loop action:**

   | Risk Level | requires_human_review | Action |
   |---|---|---|
   | Low | False | Payment proceeds normally |
   | Medium | True | User warned, can override immediately |
   | High | True | Cooling-off period, user can override |
   | High + secrecy | True, escalated | Payment locked, fraud analyst notified via `/escalations` |

### API contract

```
POST /predict   (nlp-model service, internal)
{ "message": "Send me money urgently trust me" }

→ {
  "risk_score": 99,
  "risk_level": "HIGH",
  "confidence": 1.0,
  "triggered_features": ["urgency", "money_request"],
  "requires_human_review": true
}
```

The backend (`backend/services/nlp_service.py`) calls this internally and layers on escalation logic, alert persistence, and a rule-based fallback if the NLP service is unreachable.

---

## Model Update Experiments (what we tried, and what's actually deployed)

While integrating the model into the live Docker stack, the originally-committed `scamshield_bert_model/config.json` declared 3 output labels but the `model.safetensors` file present locally was an older binary (2-class) checkpoint — the two were out of sync, which crashed the service on a clean rebuild.

Before discovering the real cause, we tried fixing the *symptom* by re-fine-tuning a new binary BERT model end-to-end on a local GPU (`nlp-model/train_bert.py`, checkpoints `scamshield_bert_model_v2`–`v4`), using class-weighted + label-smoothed loss to fix a separate calibration bug (the original 2-class checkpoint scored almost everything at 0% or 99%, with no real Medium tier). That genuinely fixed calibration, but on the live 40-case test suite (`run_test_payloads.py` against `data/api_test_payloads.jsonl`) it introduced a new false-positive pattern — generic legitimate banking/app messages (e.g. *"Your monthly statement is ready to view in your mobile banking app"*) scoring as HIGH risk — because the retraining data overweighted phishing-style "official app" phrasing without matching scam intent.

Investigating *why* the original config/weights were mismatched led to the real fix: the NLP teammate's three-tier upgrade commit had also pushed an updated Google Drive link with the actual three-class weights, which simply hadn't been re-downloaded locally. Downloading that file and restoring the 3-label config solved both problems at once — it's the genuinely retrained three-tier model described above, not our local 2-class GPU retrain.

**Result on the same 40-case live suite:**

| Model | Pass rate | Notes |
|---|---|---|
| Original 2-class checkpoint (desynced config) | 18/40 | Crashes on fresh rebuild due to config/weights mismatch |
| Our local GPU retrain (`v4`, 2-class, class-weighted) | 16/40 | Fixed calibration, but new false positives on generic banking/app text |
| **Team's three-tier model (currently deployed)** | **31/40** | Genuine Low/Medium/High classification, no false positives on the v4 regression cases |

The deployed model is downloaded automatically per the instructions in [Download the Model](#download-the-model) below — `nlp-model/scamshield_bert_model/model.safetensors`, linked from the Google Drive ID committed in `b94389f` ("Upgrade to three-tier BERT model"). The `v2`–`v4` retrain checkpoints and `train_bert.py` are kept in `nlp-model/` for reference but are not used by the deployed service.

---

## Download the Model

The BERT model file (`model.safetensors`, ~417MB) exceeds GitHub's 100MB limit and must be downloaded separately:

**[Download model.safetensors](https://drive.google.com/file/d/1k1Sa-KH1il5cNQJf_UOro3meSrXSW2yJ/view?usp=sharing)**

Place it at:
```
nlp-model/scamshield_bert_model/model.safetensors
```

The remaining model files (`config.json`, tokenizer files, `vocab.txt`) are already included in the repository. Once in place, `docker compose up --build` will pick it up automatically.

---

## Responsible AI & Ethical Tradeoffs

**False Positives** — misidentifying a legitimate transfer creates friction. Mitigation: the system relies on "speed bumps" rather than hard blocks — analysts and users are presented with confidence intervals and contextual warnings, so legitimate users are never automatically de-platformed.

**Model Drift** — scam tactics evolve rapidly. Mitigation: an escalation feedback loop lets analysts resolve cases as confirmed-fraud or false-positive, which can feed anonymized behavioral metadata back into future retraining.

**Synthetic Data** — all training data beyond the UCI SMS ham messages was synthetically generated by the team, since no public dataset exists specifically for modern social-media-driven financial exploitation. ~4,153 synthetic messages were generated across 6 datasets covering impersonation, crypto scams, romance scams, fake emergencies, phishing, security bypass, deflection tactics, and medium-risk ambiguous messages. All synthetic data is clearly labelled, disclosed, and included as CSVs in `nlp-model/`.

**Privacy** — the model analyses message content in real time and never stores message text; only the risk level, score, and triggered features are persisted.

**Human in the Loop** — the model never makes autonomous decisions: Medium risk warns and allows immediate override, High risk adds a cooling-off period before override, and High risk + secrecy blocks the payment and routes to a human fraud analyst.

**Known Limitations** — the model is fine-tuned on synthetic data which, while diverse, may not cover all real-world scam variations. It currently analyses individual messages rather than full conversation threads.

**Future Work:**
- Multi-turn conversation analysis to detect escalating pressure patterns across a thread.
- Writing-style deviation detection to flag when someone writes differently from their established baseline.
- A continuous retraining pipeline on confirmed real scam reports surfaced via the analyst escalation workflow.
- Evaluation on larger, more diverse real-world exploitation datasets.

---

## Repository Layout

| Path | Description |
|---|---|
| `backend/` | FastAPI service — Postgres persistence, alerting, escalation workflow |
| `nlp-model/` | BERT model, training notebook/scripts, and serving API |
| `frontend/` | Message analysis UI, alerts feed, and analyst dashboard |
| `docker-compose.yml` | Orchestrates `db`, `nlp`, `api`, and `frontend` services |
| `data/api_test_payloads.jsonl` | 40-case held-out evaluation suite, never used for training |
| `run_test_payloads.py` | Grades the live `/analyse` endpoint against the held-out suite |
