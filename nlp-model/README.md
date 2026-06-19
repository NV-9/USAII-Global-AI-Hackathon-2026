# ScamShield AI - NLP Model

## Overview
This module contains the Natural Language Processing (NLP) model that forms 
the core intelligence layer of ScamShield AI. It analyses text messages and 
conversations to detect digital exploitation patterns including financial scams, 
social media impersonation, psychological manipulation tactics, and phishing attempts.

The model takes a message as input and returns a risk score, risk level, 
confidence score, triggered features, and escalation flags, which the backend 
API uses to trigger cross-platform alerts and human review workflows.

---

## Model Performance

| Metric | Score |
|---|---|
| Overall Accuracy | 96% (local CPU) / 100% (GPU) |
| Validation Accuracy | 99.9% |
| Validation Precision | 100% |
| Validation Recall | 99.7% |
| F1 Score | 99.9% |

Evaluated on 50 diverse real-world scam messages covering 5 scam categories 
and legitimate messages including tricky edge cases (money requests between 
friends, casual urgent messages).

---

## Model Architecture

The final model is a **fine-tuned BERT (bert-base-uncased)** classifier for 
sequence classification with 2 output labels (legitimate / scam).

BERT was chosen over TF-IDF + Logistic Regression because it understands 
context and meaning rather than just word frequency. This allows it to detect 
scams that deliberately avoid obvious trigger words, for example:

- "omg it's me, I lost my phone, can you spot me fifty quid" : no keywords but clear impersonation pattern
- "been quietly stacking gains on this platform, want the link" : no "invest" or "profit" but clear crypto scam
- "so this is awkward but they won't release my car without payment" : no "urgent" but clear fake emergency

TF-IDF missed these entirely. BERT catches them because it learned the 
underlying conversational patterns of exploitation, not just the vocabulary.

---

## Development Journey

We took an iterative approach to building this model:

**Phase 1 - TF-IDF + Logistic Regression baseline**
Built an initial model using TF-IDF vectorisation and Logistic Regression 
trained on UCI SMS Spam Collection and Kaggle Scam Detection datasets. 
Achieved 98% overall accuracy but struggled with modern scam patterns,
particularly social media impersonation and indirect romance scams that 
avoid obvious keywords.

**Phase 2 - Synthetic data generation**
Identified that both datasets were SMS spam collections from 2011 that 
lacked modern digital exploitation patterns. Generated 2,700 synthetic scam 
conversations across 5 categories with structural variety — different tones, 
sentence structures, and phrasing styles, specifically including examples 
that avoid trigger keywords to force the model to learn deeper patterns.

**Phase 3 - Switch to BERT**
Fine-tuned bert-base-uncased on the cleaned dataset using a Tesla T4 GPU. 
Through rigorous testing on 50 diverse messages, BERT demonstrated 
significantly stronger generalisation than TF-IDF, particularly on casual 
impersonation, indirect romance scams, and crypto scams without obvious 
financial keywords.

**Phase 4 - Data cleaning**
Identified that mixing heterogeneous datasets (generic SMS spam + financial 
exploitation scams) caused inconsistent label mapping. Resolved by training 
exclusively on synthetic scam data plus clean legitimate messages, producing 
a consistent and reliable model.

This iterative process : building, testing, identifying weaknesses, and 
improving, is documented transparently as part of our responsible AI approach.

---

## Training Data

| Dataset | Messages | Purpose |
|---|---|---|
| Synthetic Scam Dataset v1 | 1,300 (1,000 scam / 300 legit) | Initial modern scam patterns |
| Synthetic Scam Dataset v2 | 1,400 (1,100 scam / 300 legit) | Diverse phrasing, avoids keyword reliance |
| UCI SMS Ham Messages | 4,690 legitimate messages | Clean legitimate baseline |
| **Total** | **6,438 messages** | **1,748 scam / 4,690 legitimate** |

All synthetic data was team-generated and is fully disclosed. Both synthetic 
dataset files are included in this repository.

---

## How It Works

### Step 1 - Input
A message string is passed to `analyse_message()`.

### Step 2 - BERT Classification
The message is tokenised using BertTokenizer and passed through the 
fine-tuned BERT model, which outputs a probability score for each class.

### Step 3 - Custom Feature Extraction (Explainability)
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

### Step 4 — Risk Scoring & Escalation
Risk score is calculated from BERT's confidence probability:

| Risk Level | Score | Action |
|---|---|---|
| Low | 0–39 | Message appears legitimate : no action |
| Medium | 40–69 | Suspicious : user warned, can override |
| High | 70–89 | High risk : cooling off period before override |
| Critical (escalate) | 90–100 + secrecy detected | Blocked : escalated to fraud analyst |

### Step 5 — Output
```json
{
  "risk_score": 97,
  "risk_level": "High",
  "confidence": 0.98,
  "triggered_features": ["urgency", "money_request", "secrecy_tactics"],
  "requires_human_review": true,
  "escalate_to_analyst": false
}
```

---

## Example Outputs

**Example 1 : Obvious Scam:**
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
#   "risk_score": 0, "risk_level": "Low", "confidence": 0.0,
#   "triggered_features": [],
#   "requires_human_review": False, "escalate_to_analyst": False
# }
```

**Example 3 : Social Media Impersonation (no obvious keywords):**
```python
analyse_message("omg you won't believe this, it's James, phone died using a mates, can you spot me fifty quid")
# {
#   "risk_score": 99, "risk_level": "High", "confidence": 1.0,
#   "triggered_features": ["suspicious_language_pattern"],
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
#   "risk_score": 0, "risk_level": "Low", "confidence": 0.0,
#   "triggered_features": [],
#   "requires_human_review": False, "escalate_to_analyst": False
# }
```

---

## Download the Model

The BERT model file (`model.safetensors`) is 417MB and exceeds GitHub's 
100MB file size limit. Download it separately and place it in the 
`scamshield_bert_model/` folder before running the notebook.

**Download:** [Add Google Drive link here]

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
| scamshield_nlp.ipynb | Main Jupyter notebook : full BERT pipeline |
| scamshield_bert_model/ | Fine-tuned BERT model folder (model.safetensors downloaded separately) |
| scamshield_model.pkl | TF-IDF model (baseline : kept for reference) |
| tfidf_vectorizer.pkl | TF-IDF vectorizer (baseline : kept for reference) |
| synthetic_scam_data.csv | Synthetic dataset v1 (1,300 messages) |
| synthetic_scam_data_v2.csv | Synthetic dataset v2 (1,400 messages, more diverse) |
| test_set_50.csv | 50-message evaluation set used for model comparison |
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

The backend service (Person 2) loads the BERT model and wraps 
`analyse_message` into a REST API endpoint.

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
  "risk_score": 87,
  "risk_level": "High",
  "confidence": 0.87,
  "triggered_features": ["urgency", "money_request"],
  "requires_human_review": true,
  "escalate_to_analyst": false
}
```

---

## Responsible AI & Data Disclosure

**Model:** Fine-tuned BERT (bert-base-uncased). A transformer-based model 
was chosen over simpler approaches because it understands contextual meaning, 
not just keyword frequency — making it harder for scammers to evade detection 
by rephrasing messages. Known limitation: the model was fine-tuned on 
synthetic data which, while diverse, may not cover all real-world scam 
variations. Continuous retraining on confirmed real scam reports is the 
identified next step.

**Synthetic Data:** 2,700 messages in the training dataset were synthetically 
generated by the team across two versions (v1 and v2). This was necessary 
because no publicly available dataset exists specifically for modern digital 
financial exploitation patterns on social media platforms. All synthetic data 
is clearly labelled and disclosed. Both CSV files are included in the repository.

**Privacy:** The model analyses message content in real time and never stores 
message text. Only the risk score and triggered features are retained.

**Human in the Loop:** The model never makes autonomous decisions. Medium and 
High risk flags require user confirmation after a cooling-off period. Critical 
cases (risk score 90+ with secrecy tactics detected) are escalated to a human 
fraud analyst and cannot be overridden by the user.

**False Positives:** Legitimate urgent money requests between friends (rent, 
splitting bills) are correctly identified as low risk. False positive rate is 
tracked as a primary performance metric and explained alerts allow users to 
override incorrect flags.

**Future Work:** BERT fine-tuning with larger, more diverse real-world scam 
datasets; writing style deviation detection to flag when someone writes 
differently from their established communication pattern; multi-turn 
conversation analysis to detect escalating pressure across multiple messages.

---

## Download the Model

The BERT model file (`model.safetensors`) is 417MB and exceeds GitHub's 
100MB file size limit. Download it separately and place it in the 
`scamshield_bert_model/` folder before running the notebook.

https://drive.google.com/file/d/1k1Sa-KH1il5cNQJf_UOro3meSrXSW2yJ/view?usp=sharing

## Built By
Sukhnaaz Kaur : NLP & AI Model

Team Ctrl Alt Elite : USAII Global AI Hackathon 2026