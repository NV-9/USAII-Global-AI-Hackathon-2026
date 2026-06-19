# ThinkAgainAI — End-to-End Testing Checklist

## 1. Setup checks

- [ ] Repository opens without broken links.
- [ ] Backend starts successfully.
- [ ] NLP service starts successfully.
- [ ] Frontend/dashboard starts successfully, once Aaron pushes it.
- [ ] API docs are reachable at `/docs`.
- [ ] Health endpoint returns status `ok`.
- [ ] No secrets, API keys, passwords, or private tokens are committed.

## 2. `/analyse` checks

For each selected test case:

- [ ] Send message to `/analyse`.
- [ ] Confirm response includes `analysis_id`.
- [ ] Confirm response includes `risk_score`.
- [ ] Confirm response includes `risk_level`.
- [ ] Confirm response includes `confidence`.
- [ ] Confirm response includes `triggered_features` or feature scores.
- [ ] Confirm response includes `recommended_action`.
- [ ] Confirm response includes `requires_human_review`.
- [ ] Confirm high-risk cases return `alert_triggered=true`.
- [ ] Confirm low-risk cases return `alert_triggered=false`.

## 3. Alert checks

- [ ] High-risk case creates an `alert_id`.
- [ ] `/alerts` lists the alert.
- [ ] Alert shows which simulated platforms were notified.
- [ ] Alert payload contains risk metadata, not full raw message content.
- [ ] Alert status is shown as simulated/sent/failed clearly.

## 4. Feedback loop checks

- [ ] Submit `confirm` for a true scam.
- [ ] Submit `dismiss` for a false positive.
- [ ] Submit `escalate` for a borderline case.
- [ ] Submit `override` for a user proceeding after warning.
- [ ] `/feedback` lists recent feedback records.
- [ ] System response explains what happened after feedback.

## 5. Frontend/dashboard checks

To complete once Aaron is done:

- [ ] User/operator can enter or view a message/case.
- [ ] Dashboard displays risk score clearly.
- [ ] Dashboard displays risk level clearly.
- [ ] Dashboard displays explanation/triggered features.
- [ ] HIGH risk is visually distinct from LOW risk.
- [ ] Alert status is visible.
- [ ] Human action buttons are visible: confirm, dismiss, escalate, override.
- [ ] The dashboard does not show claims that are not implemented.
- [ ] The demo path can be completed in under 2 minutes.

## 6. Responsible AI checks

- [ ] System is described as decision-support, not autonomous enforcement.
- [ ] Submission states non-goals: no surveillance, no automatic freezing, no plaintext message storage.
- [ ] False positives are acknowledged.
- [ ] Human review is required for serious cases.
- [ ] Synthetic data use is disclosed.
- [ ] Model drift and retraining are mentioned as lifecycle concerns.

## 7. Video checks

- [ ] Video length is 3–5 minutes.
- [ ] Shows problem and stakeholder.
- [ ] Shows AI architecture.
- [ ] Shows at least one live/recorded walkthrough.
- [ ] Shows responsible AI tradeoff.
- [ ] Demo link works.
- [ ] GitHub link works.
- [ ] Audio is clear.
- [ ] Final Devpost submission is not left until the last minute.

