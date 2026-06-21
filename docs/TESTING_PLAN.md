# SafeGuard Ai — Person 4 Testing Plan

Owner: Emmanuel  
Role: Data + Testing + Video

## Purpose

This testing pack checks whether SafeGuard Ai can classify scam-like and safe financial conversations, explain the risk reason, trigger simulated cross-platform alerts for high-risk cases, and preserve human decision-making.

The tests are built around the challenge requirement that the system should convert fragmented signals into explainable decision support for human operators, rather than acting as an autonomous surveillance or blocking system.

## Files in this pack

- `data/synthetic_test_cases.csv` — 40 synthetic test cases.
- `data/api_test_payloads.jsonl` — API-ready payloads for `/analyse`.
- `docs/testing_evidence_log.csv` — template for recording actual results.
- `docs/END_TO_END_CHECKLIST.md` — checklist for backend, model, frontend, alerts, feedback, and demo.
- `docs/API_SMOKE_TESTS.md` — curl commands for manual backend testing.
- `docs/VIDEO_SCRIPT_3_TO_5_MIN.md` — script for the final pitch/demo video.
- `docs/DEVPOST_DRAFT_FIELDS.md` — draft Devpost answers and wording.
- `README_TESTING_SECTION.md` — testing section that can be pasted into the main repo README.

## Test categories

| Category | Test IDs | Purpose |
|---|---|---|
| High-risk scam | TC001-TC010 | Confirm obvious scams are scored highly and trigger alerts |
| Medium-risk suspicious | TC011-TC015 | Confirm ambiguous messages are flagged for review, not over-blocked |
| Low-risk safe | TC016-TC020 | Confirm normal messages do not trigger unnecessary alerts |
| False-positive stress | TC021-TC024 | Show awareness of legitimate money messages |
| Adversarial scam | TC025-TC030 | Test scams that avoid obvious keywords |
| End-to-end API | TC031-TC032 | Confirm `/analyse` behaviour and alert routing |
| Feedback loop | TC033-TC036 | Confirm confirm/dismiss/escalate/override actions |
| Edge cases | TC037-TC040 | Test validation, long input, informal language, ambiguity |

## Pass/fail rules

A test passes if the system behaviour matches the expected outcome closely enough for a prototype:

1. High-risk scam messages should receive HIGH or CRITICAL risk and trigger an alert.
2. Medium-risk suspicious messages should be flagged for review, even if no alert is triggered.
3. Safe messages should not trigger cross-platform alerts.
4. False positives should be explainable and dismissible through feedback.
5. The system should not permanently block or freeze funds automatically.
6. Alert payloads should avoid storing or broadcasting raw message content.
7. The response should include human-readable triggered features or an explanation.
8. Any failure should be recorded honestly as a limitation or future improvement.

## Evidence to collect

For the final README/video, collect:

- Screenshot of `/docs` showing backend routes.
- Screenshot or recording of a HIGH-risk message being analysed.
- Screenshot or recording of the alert result.
- Screenshot or recording of feedback being submitted.
- Screenshot or recording of a LOW-risk message not triggering an alert.
- Filled `testing_evidence_log.csv` with at least 10 manually tested cases.
- Notes on at least 2 limitations or false-positive/false-negative risks.

## Recommended minimum tests before submission

Run these first if time is short:

- TC001 — friend impersonation emergency
- TC003 — fake bank safe-account scam
- TC005 — crypto investment pressure
- TC008 — fake university fee link
- TC016 — normal rent reminder
- TC017 — friend small loan without pressure
- TC021 — emergency but legitimate wording
- TC025 — adversarial wording
- TC031 — high-risk triggers alert record
- TC036 — override attempt

