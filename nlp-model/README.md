# ScamShield AI — NLP Model

## Overview
This module contains the Natural Language Processing (NLP) model that forms 
the core intelligence layer of ScamShield AI. It analyses text messages and 
conversations to detect digital exploitation patterns including financial scams, 
social media impersonation, and psychological manipulation tactics.

The model takes a message as input and returns a risk score, risk level, 
confidence score, and a list of triggered features — which the backend API 
uses to trigger cross-platform alerts.

---

## Model Performance

| Metric | Score |
|---|---|
| Overall Accuracy | 99% |
| Scam Precision | 91% |
| Scam Recall | 98% |
| F1 Score | 95% |
| False Negative Rate | 1.9% |

The model was trained on 8,272 messages and tested on 2,068 messages.

---

## How It Works

### Step 1 — Data
The model was trained on two combined datasets:
- UCI SMS Spam Collection (5,572 messages)
- Kaggle Scam Detection Dataset (5,574 messages)

After cleaning and removing duplicates, the final dataset contains 
10,340 messages — 9,034 legitimate and 1,306 scam messages.

### Step 2 — Feature Extraction
The model uses two types of features:

**TF-IDF Features (5,000 features)**
Converts message text into numerical vectors based on word importance 
across the entire dataset.

**Custom Scam-Specific Features (7 features)**
These are specifically designed to detect digital exploitation patterns:

| Feature | What It Detects |
|---|---|
| urgency_count | Time pressure language ("do it now", "limited time") |
| pressure_count | Reassurance tactics ("trust me", "don't worry") |
| money_request_count | Financial requests ("send money", "transfer", "crypto") |
| suspicious_links | URLs and suspicious links in messages |
| secrecy_count | Isolation tactics ("don't tell anyone", "between us") |
| message_length | Total character count of message |
| word_count | Total word count of message |

### Step 3 — Model
The classifier is a **Logistic Regression** model trained with 
class_weight='balanced' to handle the imbalanced dataset (more legitimate 
messages than scam messages).

### Step 4 — Output
The model outputs a structured risk assessment:

```json
{
  "risk_score": 96,
  "risk_level": "High",
  "confidence": 0.96,
  "triggered_features": ["urgency", "pressure_tactics", "money_request"],
  "requires_human_review": true
}
```

**Risk Levels:**
-  Low — risk score 0–39 — message appears legitimate
-  Medium — risk score 40–69 — suspicious, requires human review
-  High — risk score 70–100 — high probability of exploitation attempt

---

## Why NLP Over Rule-Based Systems

Rule-based systems detect only known patterns — for example blocking messages 
containing specific words like "crypto" or "transfer now". They are brittle 
and easily bypassed as scammers constantly evolve their language.

This NLP model learns statistical relationships across thousands of examples 
of exploitation language. It can detect new manipulation tactics even when 
exact words change — because it classifies on underlying linguistic and 
behavioural patterns rather than fixed rules.

---

## Files

| File | Description |
|---|---|
| scamshield_nlp.ipynb | Main Jupyter notebook — full pipeline |
| scamshield_model.pkl | Saved trained model |
| tfidf_vectorizer.pkl | Saved TF-IDF vectorizer |
| requirements.txt | Python libraries required |
| spam.csv | UCI SMS Spam Collection dataset |
| SMS Spam Dataset.csv | Kaggle Scam Detection dataset |
| README.md | This file |

---

## How to Run

### Prerequisites
Make sure you have Python 3.11+ installed.

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Open the notebook
```bash
jupyter notebook scamshield_nlp.ipynb
```
Or open directly in VS Code by clicking scamshield_nlp.ipynb

### Step 3 — Run all cells
Run all cells in order from top to bottom using Shift + Enter

### Step 4 — Use the analyse_message function
```python
result = analyse_message("Your message here")
print(result)
```

---

## Using the Saved Model

To load and use the saved model without running the full notebook:

```python
import pickle
import scipy.sparse as sp

# Load model and vectorizer
with open('scamshield_model.pkl', 'rb') as f:
    model = pickle.load(f)

with open('tfidf_vectorizer.pkl', 'rb') as f:
    tfidf = pickle.load(f)

# Use the analyse_message function from the notebook
result = analyse_message("Send me money urgently, trust me don't tell anyone")
print(result)
```

---

## Example Outputs

**Example 1 — High Risk Scam:**
```python
analyse_message("URGENT! Send money now to my account. Trust me don't worry. Limited time!")
# Output:
# {
#   "risk_score": 96,
#   "risk_level": "High", 
#   "confidence": 0.96,
#   "triggered_features": ["urgency", "pressure_tactics", "money_request"],
#   "requires_human_review": True
# }
```

**Example 2 — Legitimate Message:**
```python
analyse_message("Hey, are we still meeting for lunch tomorrow?")
# Output:
# {
#   "risk_score": 2,
#   "risk_level": "Low",
#   "confidence": 0.02,
#   "triggered_features": [],
#   "requires_human_review": False
# }
```

**Example 3 — Social Media Impersonation:**
```python
analyse_message("Hi it's me, transfer money urgently, don't tell anyone please")
# Output:
# {
#   "risk_score": 64,
#   "risk_level": "Medium",
#   "confidence": 0.65,
#   "triggered_features": ["urgency", "money_request", "secrecy_tactics"],
#   "requires_human_review": True
# }
```

---

## API Integration

The backend service (Person 2) loads the saved model files and wraps the 
analyse_message function into a REST API endpoint.

**Expected API call:**
```json
POST /analyse
{
  "message": "Send me money urgently trust me"
}
```

**Expected API response:**
```json
{
  "risk_score": 87,
  "risk_level": "High",
  "confidence": 0.87,
  "triggered_features": ["urgency", "money_request"],
  "requires_human_review": true
}
```

---

## Built By
Sukhnaaz Kaur 

Team Ctrl Alt Elite — USAII Global AI Hackathon 2026