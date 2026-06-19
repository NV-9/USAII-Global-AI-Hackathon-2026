# USAII-Global-AI-Hackathon-2026 | Graduate Track | Direction A: Safe Passage

ScamShield AI is an early-warning detection system designed for Trust & Safety teams and fraud analysts at financial institutions. It identifies digital exploitation, specifically financial coercion and impersonation scams, by analyzing cross-platform behavioral and linguistic signals.

Unlike traditional rule-based systems that scammers easily bypass by altering keywords, ScamShield AI utilizes advanced NLP to detect semantic intent, urgency, and manipulative pressure. It surfaces these insights into an explainable dashboard, empowering human analysts to make informed intervention decisions before funds are irrevocably lost.

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
| Backend API test suite (40 cases) | 85% (33/39) |

### Training data

The model was trained on 7,649 messages across three risk tiers. All training data beyond UCI SMS ham messages was synthetically generated by the team, this was necessary because no publicly available dataset exists for modern digital financial exploitation on social media platforms. All synthetic data is transparently disclosed and included in the repository.

### Explainability

Alongside the BERT prediction, the model extracts specific triggered features in plain language, so users and analysts understand exactly why a message was flagged, not just that it was. Features include urgency language, pressure tactics, money requests, suspicious links, secrecy/isolation tactics, and suspicious language patterns detected by BERT without explicit keywords.

---

## Key Features

**Semantic Intent Detection:** Outperforms heuristic keyword-matching by evaluating the contextual weight of linguistic features using a fine-tuned transformer model.

**Three-Tier Risk Classification:** Moves beyond binary scam/not-scam to Low/Medium/High risk levels, enabling proportionate human intervention rather than binary block/allow decisions.

**Cross-Platform Pub/Sub Alerting:** Simulates a centralised registry where payment platforms subscribe to risk-score webhooks generated by upstream messaging platforms — closing the gap that allows scammers to bypass a block on one platform by switching to another.

**Explainable AI (XAI):** Highlights the specific manipulation tactics detected (urgency, secrecy, pressure, impersonation signals) to accelerate human review and support informed override decisions.

**Responsible AI Guardrails:** Analyses payloads in real time and destroys raw input immediately after scoring. Only risk scores and feature labels are retained, never message content.

**Human-in-the-Loop by Design:** The AI never makes autonomous financial decisions. Every flagged transaction requires human confirmation, with escalated cases routed to trained fraud analysts.

---

## Responsible AI & Ethical Tradeoffs

**False Positives:** Misidentifying a legitimate transfer creates friction and erodes user trust. Mitigation: The system uses a three-tier approach rather than binary blocking. Medium risk cases show a soft warning the user can immediately override. High risk cases enforce a brief cooling-off period. Only escalated cases (High risk + isolation tactics detected) are blocked pending analyst review. All alerts include plain-language explanations of what was detected.

**Model Drift:** Scam tactics evolve rapidly, a model trained today will degrade as new exploitation techniques emerge. Mitigation: The system incorporates a feedback loop where confirmed scam reports and analyst overrides feed back into the training pipeline. Precision, recall, and false positive rates are tracked continuously as primary performance metrics.

**Adversarial Robustness:** Sophisticated scammers may learn what patterns trigger the model and adapt their language. Mitigation: BERT's contextual understanding makes it significantly harder to evade than keyword-based systems. Regular red-teaming, deliberately attempting to bypass the model, is built into the maintenance process.

**Privacy:** Message content is never stored. Only the mathematical risk score and triggered feature labels are retained and broadcast. Users provide explicit informed consent before the system activates.

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