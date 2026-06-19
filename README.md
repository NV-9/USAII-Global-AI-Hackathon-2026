# USAII-Global-AI-Hackathon-2026 | Graduate Track | Direction A: Safe Passage

ThinkAgainAI is an early-warning detection system designed for Trust & Safety teams and fraud analysts at financial institutions. It identifies digital exploitation, specifically financial coercion and impersonation scams, by analyzing cross-platform behavioral and linguistic signals.

Unlike traditional rule-based systems that scammers easily bypass by altering keywords, ThinkAgainAI utilizes advanced NLP to detect semantic intent, urgency, and manipulative pressure. It surfaces these insights into an explainable dashboard, empowering human analysts to make informed intervention decisions before funds are irrevocably lost.

---

## The Problem & Our Scope

Victims of social media impersonation scams often bypass standard banking warnings because they believe they are communicating with trusted friends or family. Furthermore, fraudsters exploit the fragmented digital landscape, initiating manipulation on Platform A (e.g., a messaging app) and extracting payment on Platform B (e.g., a banking app).

**What This System Does:**
- Synthesizes fragmented, multi-platform signals into a unified risk score
- Provides Explainable AI (XAI) insights to fraud analysts, detailing why a transaction is flagged
- Prioritizes high-risk cases for manual human review using a three-tier classification system

**What This System Does NOT Do (Non-Goals):**
- No Surveillance: It does not monitor general user conversations or read private messages at rest
- No Automated Freezes: It does not automatically freeze accounts or block funds, human operators retain final decision-making authority
- No PII Storage: It does not store plaintext conversational data

---

## System Architecture

Our architecture bridges the gap between fragmented data and human intervention through five layers:

1. **Data Layer (Simulated):** Ingests transient, anonymized metadata and text snippets via a cross-platform API webhook
2. **Intelligence Layer (NLP):** A fine-tuned BERT transformer model analyses the payload for coercion markers (temporal urgency, guilt-tripping syntax, secrecy tactics, deflection patterns) and produces a three-tier risk classification (Low / Medium / High)
3. **Governance Layer (Privacy):** Employs a zero-retention policy. Text is processed in memory and only a localised risk score and triggered features are broadcast to the registry, never the message content
4. **Decision Support Layer (UI):** Surfaces the risk level, triggered features, and recommended action to the Trust & Safety analyst dashboard
5. **Human Action Layer:** All final decisions remain with humans, medium risk cases show a warning the user can override, high risk cases enforce a cooling-off period, and escalated cases are routed directly to a fraud analyst

All four services run via `docker-compose.yml`, with healthchecks gating startup order so the API waits on Postgres and the frontend waits on a healthy API:

| Service | Container | Local URL |
|---|---|---|
| Frontend | `frontend` | http://localhost:3000 |
| Backend API | `api` | http://localhost:8000 |
| NLP Service | `nlp` | http://localhost:8001 |
| Database | `db` (Postgres) | internal only, port 5432 |

---

## NLP Model : Intelligence Layer

**Model:** Fine-tuned BERT (bert-base-uncased) with three output classes

The NLP model is the core of the intelligence layer. It was built and trained specifically for modern digital financial exploitation patterns, not generic spam detection.

### Why BERT over rule-based systems

Rule-based systems block messages containing specific keywords like "transfer now" or "don't tell anyone." Scammers bypass these trivially by rephrasing. Our BERT model learns the underlying intent and context of exploitation, detecting scams even when obvious keywords are absent:

- "omg it's me on a borrowed phone, can you spot me fifty quid" : no keywords, clear impersonation
- "been quietly stacking gains on this platform, want the link" : no "invest", clear crypto scam
- "Stop asking questions. Just send the money. I'll explain later." : deflection tactic, no financial keywords
- "When you pay, choose family and friends and ignore any fraud warning." : security bypass instruction

### Three-tier risk classification

The model outputs one of three risk levels — not a binary scam/not-scam decision. This enables proportionate human-in-the-loop responses:

| Risk Level | Action | Human Role |
|---|---|---|
| Low | Payment proceeds normally | No intervention needed |
| Medium | User warned, can override immediately | User makes informed decision |
| High | Cooling off period before override allowed | User makes decision after pause |
| High + secrecy detected | Payment blocked | Fraud analyst reviews and decides |

### Model output

```json
{
  "risk_score": 99,
  "risk_level": "High",
  "confidence": 1.0,
  "triggered_features": ["urgency", "secrecy_tactics"],
  "requires_human_review": true,
  "escalate_to_analyst": true
}
```

### Performance

| Test | Result |
|---|---|
| 80 diverse real-world messages | 97% accuracy |
| HIGH risk detection | 100% (26/26) |
| MEDIUM risk detection | 96% (26/27) |
| LOW risk detection | 96% (26/27) |
| Backend API test suite (40 cases), as last verified against the deployed model | 78% (31/40) |

### Training data

The model was trained on 7,649 messages across three risk tiers. All training data beyond UCI SMS ham messages was synthetically generated by the team, this was necessary because no publicly available dataset exists for modern digital financial exploitation on social media platforms. All synthetic data is transparently disclosed and included in the repository.

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

**Label key:** 0 = Low risk (legitimate), 1 = Medium risk (suspicious but ambiguous), 2 = High risk (clear exploitation attempt).

### Explainability

Alongside the BERT prediction, the model extracts specific triggered features in plain language, so users and analysts understand exactly why a message was flagged, not just that it was. Features include urgency language, pressure tactics, money requests, suspicious links, secrecy/isolation tactics, and suspicious language patterns detected by BERT without explicit keywords.

### `nlp-model/` Files

| File | Description |
|---|---|
| `scamshield_nlp.ipynb` | Main Jupyter notebook — full BERT training pipeline |
| `scamshield_bert_model/` | Deployed three-tier BERT model folder (`model.safetensors` downloaded separately, see [Download the Model](#download-the-model)) |
| `scamshield_bert_model_v2/`, `_v3/`, `_v4/` | Local GPU retrain checkpoints kept for reference only — not used by the deployed service |
| `train_bert.py` | GPU training script used for the `v2`-`v4` retrain experiments |
| `app.py` | FastAPI wrapper that serves the model on port 8001 |
| `scamshield_model.pkl`, `tfidf_vectorizer.pkl` | TF-IDF baseline model (kept for reference) |
| `synthetic_scam_data*.csv`, `synthetic_medium_extra*.csv` | Synthetic training datasets |
| `test_set_50.csv` | 50-message held-out evaluation set |
| `requirements.txt` | Notebook/training dependencies |
| `requirements-serve.txt` | Pinned dependencies for the `app.py` FastAPI service |

### Running the notebook

```bash
pip install -r nlp-model/requirements.txt
jupyter notebook nlp-model/scamshield_nlp.ipynb
```

Requires `nlp-model/scamshield_bert_model/model.safetensors` to be downloaded first — see [Download the Model](#download-the-model).

---

## Key Features

**Semantic Intent Detection:** Outperforms heuristic keyword-matching by evaluating the contextual weight of linguistic features using a fine-tuned transformer model.

**Three-Tier Risk Classification:** Moves beyond binary scam/not-scam to Low/Medium/High risk levels, enabling proportionate human intervention rather than binary block/allow decisions.

**Cross-Platform Pub/Sub Alerting:** Simulates a centralised registry where payment platforms subscribe to risk-score webhooks generated by upstream messaging platforms — closing the gap that allows scammers to bypass a block on one platform by switching to another.

**Explainable AI (XAI):** Highlights the specific manipulation tactics detected (urgency, secrecy, pressure, impersonation signals) to accelerate human review and support informed override decisions.

**Responsible AI Guardrails:** Analyses payloads in real time and destroys raw input immediately after scoring. Only risk scores and feature labels are retained, never message content.

**Human-in-the-Loop by Design:** The AI never makes autonomous financial decisions. Every flagged transaction requires human confirmation, with escalated cases routed to trained fraud analysts.

---

## Model Update Experiments (what we tried, and what's actually deployed)

While verifying a clean Docker rebuild, the committed `nlp-model/scamshield_bert_model/config.json` declared 3 output labels but the local `model.safetensors` file was an older binary (2-class) checkpoint — the two were out of sync, which crashed the `nlp` service on a fresh rebuild.

Before discovering the real cause, we tried fixing the *symptom* by re-fine-tuning a new binary BERT model end-to-end on a local GPU (`nlp-model/train_bert.py`, checkpoints `scamshield_bert_model_v2`–`v4`), using class-weighted + label-smoothed loss to fix a separate calibration bug (the original 2-class checkpoint scored almost everything at 0% or 99%, with no real Medium tier). That genuinely fixed calibration, but on the live 40-case test suite (`run_test_payloads.py` against `data/api_test_payloads.jsonl`) it introduced a new false-positive pattern — generic legitimate banking/app messages (e.g. *"Your monthly statement is ready to view in your mobile banking app"*) scoring as HIGH risk — because the retraining data overweighted phishing-style "official app" phrasing without matching scam intent.

Investigating *why* the original config/weights were mismatched led to the real fix: the three-tier model upgrade had also pushed an updated Google Drive link with the actual three-class weights, which simply hadn't been re-downloaded locally. Downloading that file and restoring the 3-label config solved both problems at once — it's the genuinely retrained three-tier model described above, not the local 2-class GPU retrain.

**Result on the same 40-case live suite:**

| Model | Pass rate | Notes |
|---|---|---|
| Original 2-class checkpoint (desynced config) | 18/40 | Crashes on fresh rebuild due to config/weights mismatch |
| Local GPU retrain (`v4`, 2-class, class-weighted) | 16/40 | Fixed calibration, but new false positives on generic banking/app text |
| **Three-tier model (currently deployed)** | **31/40** | Genuine Low/Medium/High classification, no false positives on the `v4` regression cases |

The deployed model is downloaded per the instructions in [Download the Model](#download-the-model) below. The `v2`–`v4` retrain checkpoints and `train_bert.py` are kept in `nlp-model/` for reference but are not used by the deployed service.

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

**False Positives:** Misidentifying a legitimate transfer creates friction and erodes user trust. Mitigation: The system uses a three-tier approach rather than binary blocking. Medium risk cases show a soft warning the user can immediately override. High risk cases enforce a brief cooling-off period. Only escalated cases (High risk + isolation tactics detected) are blocked pending analyst review. All alerts include plain-language explanations of what was detected.

**Model Drift:** Scam tactics evolve rapidly, a model trained today will degrade as new exploitation techniques emerge. Mitigation: The system incorporates a feedback loop where confirmed scam reports and analyst overrides feed back into the training pipeline. Precision, recall, and false positive rates are tracked continuously as primary performance metrics.

**Adversarial Robustness:** Sophisticated scammers may learn what patterns trigger the model and adapt their language. Mitigation: BERT's contextual understanding makes it significantly harder to evade than keyword-based systems. Regular red-teaming, deliberately attempting to bypass the model, is built into the maintenance process.

**Privacy:** Message content is never stored. Only the mathematical risk score and triggered feature labels are retained and broadcast. Users provide explicit informed consent before the system activates.

---

## Backend

**Stack:** FastAPI + asyncpg (raw SQL against Postgres, no ORM) + httpx for outbound platform webhooks.

The backend is the decision-support and persistence layer: it scores incoming messages via the NLP service, fans out alerts to payment platforms, tracks fraud-analyst escalations, and persists everything in Postgres so the dashboard reflects real history rather than in-memory state.

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/analyse` | Scores a message, broadcasts a platform alert on HIGH/CRITICAL risk, and escalates to a fraud analyst if override-abuse patterns are detected |
| `GET` | `/alerts` | Paginated list of alert broadcasts (`page`, `page_size`, plus a legacy `limit`) |
| `GET` | `/alerts/{id}` | Retrieve a specific alert record |
| `POST` | `/feedback` | Records a user/operator action: confirm, dismiss, escalate, or override |
| `GET` | `/feedback` | List recent feedback entries |
| `GET` | `/escalations` | List fraud-analyst escalations (pending by default) |
| `GET` | `/escalations/{id}` | Retrieve a specific escalation |
| `POST` | `/escalations/{id}/resolve` | Analyst confirms fraud or releases the conversation, unlocking overrides |
| `GET` | `/health` | Service health, NLP backend status, uptime |

Interactive API docs are served at `/docs` (Swagger) and `/redoc`.

### Alert broadcasting

On a HIGH or CRITICAL score, `/analyse` fans the alert out concurrently to every platform in `PLATFORM_WEBHOOKS` (PayPal, Venmo, Cash App, Revolut, Zelle, Wise) with a per-call and global timeout, then persists the result of every platform call — sent, failed, or simulated — to the `alerts` table.

### Fraud-analyst escalation

A conversation is escalated to a human analyst once its risk score exceeds a configured threshold **and** the same session has already attempted multiple overrides across multiple flagged messages — a single high-risk warning never auto-escalates. Once escalated, `is_session_locked` blocks further overrides on that session until an analyst calls `/escalations/{id}/resolve`.

### Persistence

Three Postgres tables, created on startup if missing, no migrations framework:

| Table | Stores |
|---|---|
| `alerts` | Risk score, level, per-platform delivery results, session/analysis IDs |
| `feedback` | User/operator actions (confirm, dismiss, escalate, override) per analysis |
| `escalations` | Escalation reason, status, and analyst resolution |

Message content itself is never persisted — only scores, feature labels, and outcomes.

---

## Frontend

### Features

- Paste and analyse suspicious messages
- AI-generated scam risk scoring
- Risk classification (Low, Medium, High)
- Scam indicator explanations
- Cooling-off timer for suspicious activity
- User decision workflow (Cancel or Proceed Anyway)
- Fraud analyst escalation workflow
- Recent alerts dashboard
- Responsive dark-themed interface

### Technologies

- HTML5
- CSS3
- Vanilla JavaScript

### User Flow

1. Paste a suspicious message.
2. Click **Analyse Message**.
3. Review the risk score and explanation.
4. Complete the cooling-off period for Medium and High risk cases.
5. Choose to cancel the action or proceed despite the warning.
6. High-risk cases can be escalated to a human fraud analyst for review.

### Screens

- Message Analysis Screen
- Risk Assessment Results
- Cooling-Off Decision Panel
- Fraud Analyst Escalation Screen
- Recent Alerts Dashboard

---

## Testing & Evaluation

The testing work focused on verifying the full decision-support workflow: message signal → NLP risk insight → alert decision → human action → feedback.

### Test dataset

40 synthetic test cases covering high-risk scam messages, medium-risk suspicious messages, low-risk safe messages, false-positive stress tests, adversarial scam wording, end-to-end API behaviour, feedback-loop behaviour, and edge cases. Stored in `data/synthetic_test_cases.csv` and `data/api_test_payloads.jsonl`.

### What we tested

1. Score high-risk scam messages higher than safe messages.
2. Detect behavioural features such as urgency, pressure, secrecy, money requests, suspicious links, and impersonation markers.
3. Trigger simulated cross-platform alerts for high-risk cases.
4. Avoid over-alerting safe messages.
5. Allow human feedback actions: confirm, dismiss, escalate, or override.
6. Keep the system as decision-support rather than autonomous enforcement.

### Evaluation approach

Because this is a hackathon prototype, we evaluated system behaviour using manually labelled synthetic scenarios rather than real private messages. Each test case includes an expected risk level, expected triggered features, expected alert behaviour, and expected human-review behaviour. Actual results are recorded in `docs/testing_evidence_log.csv`.

### Responsible AI testing

We included false-positive cases because misclassifying legitimate urgent payments could cause real harm. We also included adversarial cases where scammers avoid obvious words like "transfer" or "crypto," because model drift and evasion are realistic lifecycle risks.

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

---

## Team

| Person | Role |
|---|---|
| Sukhnaaz Kaur | NLP & AI Model |
| Viswamedha Nalabotu | Backend API & Alert System |
| Aaron Abraham | Frontend Dashboard |
| Emmanuel Ikelua | Data, Testing & Submission |

**Team:** Ctrl Alt Elite
**Track:** Graduate : AI for Systems & Society
**Challenge:** Brief 5, Direction A : AI Against Digital Exploitation
**Qualifier Code:** GR26-04656621
