# Testing & Evaluation

The Person 4 testing work focused on verifying the full decision-support workflow: message signal → NLP risk insight → alert decision → human action → feedback.

## Test dataset

We created 40 synthetic test cases covering:

- High-risk scam messages
- Medium-risk suspicious messages
- Low-risk safe messages
- False-positive stress tests
- Adversarial scam wording
- End-to-end API behaviour
- Feedback-loop behaviour
- Edge cases

The test cases are stored in:

- `data/synthetic_test_cases.csv`
- `data/api_test_payloads.jsonl`

## What we tested

The tests check whether ScamShield AI can:

1. Score high-risk scam messages higher than safe messages.
2. Detect behavioural features such as urgency, pressure, secrecy, money requests, suspicious links, and impersonation markers.
3. Trigger simulated cross-platform alerts for high-risk cases.
4. Avoid over-alerting safe messages.
5. Allow human feedback actions: confirm, dismiss, escalate, or override.
6. Keep the system as decision-support rather than autonomous enforcement.

## Evaluation approach

Because this is a hackathon prototype, we evaluated system behaviour using manually labelled synthetic scenarios rather than real private messages. Each test case includes an expected risk level, expected triggered features, expected alert behaviour, and expected human-review behaviour. Actual results are recorded in `docs/testing_evidence_log.csv`.

## Responsible AI testing

We included false-positive cases because misclassifying legitimate urgent payments could cause real harm. We also included adversarial cases where scammers avoid obvious words like “transfer” or “crypto,” because model drift and evasion are realistic lifecycle risks.

