# ScamShield AI - NLP Model

## Overview
This module contains the Natural Language Processing (NLP) model that forms
the core intelligence layer of ScamShield AI. It analyses text messages and
conversations to detect digital exploitation patterns including financial scams,
social media impersonation, psychological manipulation tactics, and phishing attempts.

The model takes a message as input and returns a risk level (Low / Medium / High),
confidence score, triggered features, and escalation flags, which the backend
API uses to trigger cross-platform alerts and human review workflows.

---

## Model Performance

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

Evaluated on 80 diverse messages covering all three risk tiers including
tricky edge cases, casual money requests between friends, slang and emoji
scams, indirect romance scams, and security bypass instructions.

---

## Model Architecture

The final model is a **fine-tuned BERT (bert-base-uncased)** classifier for
sequence classification with **3 output labels** (Low / Medium / High risk).

BERT was chosen over TF-IDF + Logistic Regression because it understands
context and meaning rather than just word frequency. This allows it to detect
scams that deliberately avoid obvious trigger words, for example:

- "omg it's me, I lost my phone, can you spot me fifty quid" : no keywords but clear impersonation
- "been quietly stacking gains on this platform, want the link" : no "invest" but clear crypto scam
- "so this is awkward but they won't release my car without payment" : no "urgent" but clear fake emergency
- "Stop asking questions. Just send the money. I'll explain later." : deflection tactic with no financial keywords

TF-IDF missed all of these. BERT catches them because it learned the
underlying conversational patterns of exploitation, not just the vocabulary.

---

## Development Journey

We took a fully iterative approach, documenting every stage honestly:

**Phase 1 : TF-IDF + Logistic Regression baseline**
Built an initial model using TF-IDF vectorisation and Logistic Regression
trained on UCI SMS Spam Collection and Kaggle Scam Detection datasets.
Achieved 98% overall accuracy but struggled with modern scam patterns,
particularly social media impersonation and indirect scams that avoid keywords.

**Phase 2 : Synthetic data generation (v1 and v2)**
Identified that both datasets were SMS spam from 2011 with no modern digital
exploitation patterns. Generated 2,700 synthetic scam conversations across
5 categories with genuine structural variety, different tones, phrasing styles,
and examples that deliberately avoid trigger keywords.

**Phase 3 : Switch to BERT**
Fine-tuned bert-base-uncased on a Tesla T4 GPU. Rigorous testing on 50 diverse
messages showed BERT significantly outperformed TF-IDF on casual impersonation,
indirect romance scams, and crypto scams without obvious financial keywords.

**Phase 4 : Data cleaning**
Identified that mixing heterogeneous datasets caused inconsistent label mapping.
Resolved by training exclusively on synthetic scam data plus clean UCI ham
messages, producing a consistent and reliable model.

**Phase 5 : Targeted data generation (v3)**
After testing against 40 backend test cases, identified specific failure patterns:
bank account impersonation, deflection tactics, security bypass instructions,
slang/emoji scams, and vague urgent requests. Generated 499 targeted examples
covering exactly these failure patterns.

**Phase 6 : Three-tier classification**
Upgraded from binary (scam/not scam) to three-tier classification
(Low / Medium / High risk) by creating labelled training data with genuine
medium-risk examples: messages containing one or two suspicious signals but
with plausible innocent explanations. This enables nuanced human-in-the-loop
responses rather than a binary block/allow decision.

---

## Training Data

| Dataset | Messages | Label | Purpose |
|---|---|---|---|
| Synthetic v1 | 1,300 | 0/2 | Initial modern scam patterns |
| Synthetic v2 | 1,400 | 0/2 | Diverse phrasing, avoids keyword reliance |
| Synthetic v3 (targeted) | 499 | 0/2 | Specific failure pattern fixes |
| Three-tier dataset | 624 | 0/1/2 | Medium risk examples |
| Medium extra v1 | 110 | 1 | Additional medium risk variety |
| Medium extra v2 | 120 | 1 | More medium risk patterns |
| UCI SMS Ham | 4,690 | 0 | Clean legitimate baseline |
| **Total** | **7,649** | | **Label 0: 4,942 / Label 1: 519 / Label 2: 2,188** |

**Label key:**
- 0 = Low risk (legitimate message)
- 1 = Medium risk (suspicious but ambiguous)
- 2 = High risk (clear exploitation attempt)

All synthetic data was team-generated and is fully disclosed.

---

## How It Works

### Step 1 : Input
A message string is passed to `analyse_message()`.

### Step 2 : BERT Classification
The message is tokenised using BertTokenizer and passed through the
fine-tuned BERT model, which outputs a probability distribution across
three risk classes. The class with the highest probability is selected.

### Step 3 : Custom Feature Extraction (Explainability)
Alongside the BERT prediction, custom keyword features are extracted to
provide explainable output, so users understand WHY a message was flagged:

| Feature | What It Detects |
|---|---|
| urgency | Time pressure language ("do it now", "limited time") |
| pressure_tactics | Reassurance under pressure ("trust me", "don't worry") |
| money_request | Financial requests ("send money", "transfer", "crypto") |
| suspicious_links | URLs and suspicious links |
| secrecy_tactics | Isolation tactics ("don't tell anyone", "between us") |
| suspicious_language_pattern | BERT detected scam pattern with no explicit keywords |

### Step 4 : Risk Level & Human-in-the-Loop Action

| Risk Level | BERT Output | requires_human_review | escalate_to_analyst | Action |
|---|---|---|---|---|
| Low | Class 0 | False | False | Payment proceeds normally |
| Medium | Class 1 | True | False | User warned, can override |
| High | Class 2 | True | False (usually) | Cooling off period, user can override |
| High + secrecy | Class 2 + secrecy detected | True | True | Blocked, fraud analyst notified |

### Step 5 : Output
```json
{
  "risk_score": 99,
  "risk_level": "High",
  "confidence": 1.0,
  "triggered_features": ["urgency", "money_request", "secrecy_tactics"],
  "requires_human_review": true,
  "escalate_to_analyst": true
}
```

---

## Example Outputs

**Example 1 : High Risk Scam:**
```python
analyse_message("URGENT! Send money now to my account. Trust me don't worry. Limited time offer!")
# {
#   "risk_score": 99, "risk_level": "High", "confidence": 1.0,
#   "triggered_features": ["urgency", "pressure_tactics", "money_request"],
#   "requires_human_review": True, "escalate_to_analyst": False
# }
```

**Example 2 : Legitimate Message:**
```python
analyse_message("Hey, are we still meeting for lunch tomorrow?")
# {
#   "risk_score": 99, "risk_level": "Low", "confidence": 1.0,
#   "triggered_features": [],
#   "requires_human_review": False, "escalate_to_analyst": False
# }
```

**Example 3 : Medium Risk (suspicious but ambiguous):**
```python
analyse_message("Can you send me £80 today? I need it urgently. Will explain later.")
# {
#   "risk_score": 99, "risk_level": "Medium", "confidence": 1.0,
#   "triggered_features": ["urgency"],
#   "requires_human_review": True, "escalate_to_analyst": False
# }
```

**Example 4 : Romance Scam with Escalation:**
```python
analyse_message("My darling I need your help, I am stuck at customs and need £300, please send urgently, don't tell anyone")
# {
#   "risk_score": 99, "risk_level": "High", "confidence": 1.0,
#   "triggered_features": ["urgency", "secrecy_tactics"],
#   "requires_human_review": True, "escalate_to_analyst": True
# }
```

**Example 5 : Legitimate Urgent Money Request (correctly not flagged):**
```python
analyse_message("can you send the rent money today, landlord's chasing me and I don't want a late fee")
# {
#   "risk_score": 99, "risk_level": "Low", "confidence": 1.0,
#   "triggered_features": [],
#   "requires_human_review": False, "escalate_to_analyst": False
# }
```

**Example 6 : Impersonation Scam (no obvious keywords):**
```python
analyse_message("omg it's me on a borrowed phone, I need £200 now urgently, please don't tell anyone")
# {
#   "risk_score": 99, "risk_level": "High", "confidence": 1.0,
#   "triggered_features": ["urgency", "secrecy_tactics"],
#   "requires_human_review": True, "escalate_to_analyst": True
# }
```

---

## Download the Model

The BERT model file (`model.safetensors`) is 417MB and exceeds GitHub's
100MB file size limit. Download it separately and place it in the
`scamshield_bert_model/` folder before running the notebook.

**Download model.safetensors here:**
# ScamShield AI : NLP Model

## Overview
This module contains the Natural Language Processing (NLP) model that forms
the core intelligence layer of ScamShield AI. It analyses text messages and
conversations to detect digital exploitation patterns including financial scams,
social media impersonation, psychological manipulation tactics, and phishing attempts.

The model takes a message as input and returns a risk level (Low / Medium / High),
confidence score, triggered features, and escalation flags, which the backend
API uses to trigger cross-platform alerts and human review workflows.

---

## Model Performance

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

Evaluated on 80 diverse messages covering all three risk tiers including
tricky edge cases — casual money requests between friends, slang and emoji
scams, indirect romance scams, and security bypass instructions.

---

## Model Architecture

The final model is a **fine-tuned BERT (bert-base-uncased)** classifier for
sequence classification with **3 output labels** (Low / Medium / High risk).

BERT was chosen over TF-IDF + Logistic Regression because it understands
context and meaning rather than just word frequency. This allows it to detect
scams that deliberately avoid obvious trigger words, for example:

- "omg it's me, I lost my phone, can you spot me fifty quid" : no keywords but clear impersonation
- "been quietly stacking gains on this platform, want the link" : no "invest" but clear crypto scam
- "so this is awkward but they won't release my car without payment" : no "urgent" but clear fake emergency
- "Stop asking questions. Just send the money. I'll explain later." : deflection tactic with no financial keywords

TF-IDF missed all of these. BERT catches them because it learned the
underlying conversational patterns of exploitation, not just the vocabulary.

---

## Development Journey

We took a fully iterative approach, documenting every stage honestly:

**Phase 1 : TF-IDF + Logistic Regression baseline**
Built an initial model using TF-IDF vectorisation and Logistic Regression
trained on UCI SMS Spam Collection and Kaggle Scam Detection datasets.
Achieved 98% overall accuracy but struggled with modern scam patterns,
particularly social media impersonation and indirect scams that avoid keywords.

**Phase 2 : Synthetic data generation (v1 and v2)**
Identified that both datasets were SMS spam from 2011 with no modern digital
exploitation patterns. Generated 2,700 synthetic scam conversations across
5 categories with genuine structural variety, different tones, phrasing styles,
and examples that deliberately avoid trigger keywords.

**Phase 3 : Switch to BERT**
Fine-tuned bert-base-uncased on a Tesla T4 GPU. Rigorous testing on 50 diverse
messages showed BERT significantly outperformed TF-IDF on casual impersonation,
indirect romance scams, and crypto scams without obvious financial keywords.

**Phase 4 : Data cleaning**
Identified that mixing heterogeneous datasets caused inconsistent label mapping.
Resolved by training exclusively on synthetic scam data plus clean UCI ham
messages, producing a consistent and reliable model.

**Phase 5 : Targeted data generation (v3)**
After testing against 40 backend test cases, identified specific failure patterns:
bank account impersonation, deflection tactics, security bypass instructions,
slang/emoji scams, and vague urgent requests. Generated 499 targeted examples
covering exactly these failure patterns.

**Phase 6 : Three-tier classification**
Upgraded from binary (scam/not scam) to three-tier classification
(Low / Medium / High risk) by creating labelled training data with genuine
medium-risk examples : messages containing one or two suspicious signals but
with plausible innocent explanations. This enables nuanced human-in-the-loop
responses rather than a binary block/allow decision.

---

## Training Data

| Dataset | Messages | Label | Purpose |
|---|---|---|---|
| Synthetic v1 | 1,300 | 0/2 | Initial modern scam patterns |
| Synthetic v2 | 1,400 | 0/2 | Diverse phrasing, avoids keyword reliance |
| Synthetic v3 (targeted) | 499 | 0/2 | Specific failure pattern fixes |
| Three-tier dataset | 624 | 0/1/2 | Medium risk examples |
| Medium extra v1 | 110 | 1 | Additional medium risk variety |
| Medium extra v2 | 120 | 1 | More medium risk patterns |
| UCI SMS Ham | 4,690 | 0 | Clean legitimate baseline |
| **Total** | **7,649** | | **Label 0: 4,942 / Label 1: 519 / Label 2: 2,188** |

**Label key:**
- 0 = Low risk (legitimate message)
- 1 = Medium risk (suspicious but ambiguous)
- 2 = High risk (clear exploitation attempt)

All synthetic data was team-generated and is fully disclosed.

---

## How It Works

### Step 1 : Input
A message string is passed to `analyse_message()`.

### Step 2 : BERT Classification
The message is tokenised using BertTokenizer and passed through the
fine-tuned BERT model, which outputs a probability distribution across
three risk classes. The class with the highest probability is selected.

### Step 3 : Custom Feature Extraction (Explainability)
Alongside the BERT prediction, custom keyword features are extracted to
provide explainable output, so users understand WHY a message was flagged:

| Feature | What It Detects |
|---|---|
| urgency | Time pressure language ("do it now", "limited time") |
| pressure_tactics | Reassurance under pressure ("trust me", "don't worry") |
| money_request | Financial requests ("send money", "transfer", "crypto") |
| suspicious_links | URLs and suspicious links |
| secrecy_tactics | Isolation tactics ("don't tell anyone", "between us") |
| suspicious_language_pattern | BERT detected scam pattern with no explicit keywords |

### Step 4 : Risk Level & Human-in-the-Loop Action

| Risk Level | BERT Output | requires_human_review | escalate_to_analyst | Action |
|---|---|---|---|---|
| Low | Class 0 | False | False | Payment proceeds normally |
| Medium | Class 1 | True | False | User warned, can override |
| High | Class 2 | True | False (usually) | Cooling off period, user can override |
| High + secrecy | Class 2 + secrecy detected | True | True | Blocked, fraud analyst notified |

### Step 5 : Output
```json
{
  "risk_score": 99,
  "risk_level": "High",
  "confidence": 1.0,
  "triggered_features": ["urgency", "money_request", "secrecy_tactics"],
  "requires_human_review": true,
  "escalate_to_analyst": true
}
```

---

## Example Outputs

**Example 1 : High Risk Scam:**
```python
analyse_message("URGENT! Send money now to my account. Trust me don't worry. Limited time offer!")
# {
#   "risk_score": 99, "risk_level": "High", "confidence": 1.0,
#   "triggered_features": ["urgency", "pressure_tactics", "money_request"],
#   "requires_human_review": True, "escalate_to_analyst": False
# }
```

**Example 2 : Legitimate Message:**
```python
analyse_message("Hey, are we still meeting for lunch tomorrow?")
# {
#   "risk_score": 99, "risk_level": "Low", "confidence": 1.0,
#   "triggered_features": [],
#   "requires_human_review": False, "escalate_to_analyst": False
# }
```

**Example 3 : Medium Risk (suspicious but ambiguous):**
```python
analyse_message("Can you send me £80 today? I need it urgently. Will explain later.")
# {
#   "risk_score": 99, "risk_level": "Medium", "confidence": 1.0,
#   "triggered_features": ["urgency"],
#   "requires_human_review": True, "escalate_to_analyst": False
# }
```

**Example 4 : Romance Scam with Escalation:**
```python
analyse_message("My darling I need your help, I am stuck at customs and need £300, please send urgently, don't tell anyone")
# {
#   "risk_score": 99, "risk_level": "High", "confidence": 1.0,
#   "triggered_features": ["urgency", "secrecy_tactics"],
#   "requires_human_review": True, "escalate_to_analyst": True
# }
```

**Example 5 : Legitimate Urgent Money Request (correctly not flagged):**
```python
analyse_message("can you send the rent money today, landlord's chasing me and I don't want a late fee")
# {
#   "risk_score": 99, "risk_level": "Low", "confidence": 1.0,
#   "triggered_features": [],
#   "requires_human_review": False, "escalate_to_analyst": False
# }
```

**Example 6 : Impersonation Scam (no obvious keywords):**
```python
analyse_message("omg it's me on a borrowed phone, I need £200 now urgently, please don't tell anyone")
# {
#   "risk_score": 99, "risk_level": "High", "confidence": 1.0,
#   "triggered_features": ["urgency", "secrecy_tactics"],
#   "requires_human_review": True, "escalate_to_analyst": True
# }
```

---

## Download the Model

The BERT model file (`model.safetensors`) is 417MB and exceeds GitHub's
100MB file size limit. Download it separately and place it in the
`scamshield_bert_model/` folder before running the notebook.

**Download model.safetensors here:**
https://drive.google.com/file/d/1k1Sa-KH1il5cNQJf_UOro3meSrXSW2yJ/view?usp=sharing

Place the downloaded file at:
```
nlp-model/scamshield_bert_model/model.safetensors
```

The remaining model files (config.json, tokenizer files, vocab.txt) are
already included in this repository.

---

## Files

| File | Description |
|---|---|
| scamshield_nlp.ipynb | Main Jupyter notebook — full BERT pipeline |
| scamshield_bert_model/ | Fine-tuned BERT model folder (model.safetensors downloaded separately) |
| scamshield_model.pkl | TF-IDF model (baseline — kept for reference) |
| tfidf_vectorizer.pkl | TF-IDF vectorizer (baseline — kept for reference) |
| synthetic_scam_data.csv | Synthetic dataset v1 (1,300 messages) |
| synthetic_scam_data_v2.csv | Synthetic dataset v2 (1,400 messages) |
| synthetic_scam_data_v3.csv | Synthetic dataset v3 — targeted (499 messages) |
| synthetic_scam_data_three_tier.csv | Three-tier labelled dataset (624 messages) |
| synthetic_medium_extra.csv | Additional medium risk examples (110 messages) |
| synthetic_medium_extra2.csv | Additional medium risk examples (120 messages) |
| test_set_50.csv | 50-message evaluation set |
| api_test_payloads_results.md | 40-message backend test results |
| requirements.txt | Python dependencies |
| README.md | This file |

---

## How to Run

### Prerequisites
Python 3.11+ and the following libraries:

```bash
pip install transformers torch scikit-learn pandas
```

### Step 1 : Download the model file
Download `model.safetensors` from the link above and place it in
`scamshield_bert_model/`.

### Step 2 : Open the notebook
```bash
jupyter notebook scamshield_nlp.ipynb
```

### Step 3 : Run all cells in order

### Step 4 : Use analyse_message
```python
result = analyse_message("Your message here")
print(result)
```

---

## API Integration

The backend service loads the BERT model and wraps `analyse_message`
into a REST API endpoint.

**Expected request:**
```json
POST /analyse
{
  "message": "Send me money urgently trust me"
}
```

**Expected response:**
```json
{
  "risk_score": 99,
  "risk_level": "High",
  "confidence": 1.0,
  "triggered_features": ["urgency", "money_request"],
  "requires_human_review": true,
  "escalate_to_analyst": false
}
```

**Backend handling by risk level:**
- `risk_level: "Low"` → payment proceeds, no alert shown
- `risk_level: "Medium"` → show warning, user can override immediately
- `risk_level: "High"` → show warning, cooling off period before override
- `escalate_to_analyst: true` → block payment, notify fraud analyst, user cannot override

---

## Responsible AI & Data Disclosure

**Model:** Fine-tuned BERT (bert-base-uncased) with three output classes.
A transformer-based model was chosen because it understands contextual
meaning rather than keyword frequency, making it significantly harder
for scammers to evade detection by rephrasing messages. BERT was evaluated
against TF-IDF + Logistic Regression through rigorous side-by-side testing
on 80 diverse messages, with BERT achieving 97% accuracy versus 68% for TF-IDF.

**Three-tier classification:** The model was deliberately upgraded from binary
(scam/not scam) to three-tier (Low/Medium/High) to enable proportionate
human-in-the-loop responses. Not every suspicious message warrants a full block,
Medium risk messages receive a softer warning that respects user autonomy while
still providing protection.

**Synthetic Data:** All training data beyond the UCI SMS ham messages was
synthetically generated by the team. This was necessary because no publicly
available dataset exists specifically for modern digital financial exploitation
on social media platforms. A total of 4,153 synthetic messages were generated
across 6 datasets covering impersonation, crypto scams, romance scams, fake
emergencies, phishing, security bypass instructions, deflection tactics, and
medium-risk ambiguous messages. All synthetic data is clearly labelled and
disclosed. All CSV files are included in this repository.

**Privacy:** The model analyses message content in real time and never stores
message text. Only the risk level, score, and triggered features are retained.

**Human in the Loop:** The model never makes autonomous decisions.
- Medium risk → user sees explanation and can override immediately
- High risk → user sees explanation and can override after cooling off period
- Escalated (High + secrecy) → payment blocked, human fraud analyst reviews

**False Positives:** Legitimate urgent money requests between friends (rent,
splitting bills, casual loans) are correctly identified as Low risk in testing.
Explainable alerts tell users exactly why a message was flagged, allowing
informed override decisions.

**Known Limitations:** The model was fine-tuned on synthetic data which,
while diverse, may not cover all real-world scam variations. The model
currently analyses individual messages rather than full conversation threads,
multi-turn conversation analysis is identified as a primary next development step.

**Future Work:**
- Multi-turn conversation analysis to detect escalating pressure patterns
- Writing style deviation detection to flag when someone writes differently from their baseline
- Continuous retraining pipeline on confirmed real scam reports
- Evaluation on larger, more diverse real-world exploitation datasets

---

## Built By
Sukhnaaz Kaur - NLP & AI Model

Team Ctrl Alt Elite - USAII Global AI Hackathon 2026

Place the downloaded file at:
```
nlp-model/scamshield_bert_model/model.safetensors
```

The remaining model files (config.json, tokenizer files, vocab.txt) are
already included in this repository.

---

