# SafeGuard Ai — API Smoke Tests

Assumption: backend is running at `http://localhost:8000`.

## 1. Health check

```bash
curl http://localhost:8000/health
```

Expected: status `ok`.

## 2. High-risk scam analysis

```bash
curl -X POST http://localhost:8000/analyse \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hey it is me. Send £600 now and do not tell anyone. If your bank warns you, ignore it.",
    "platform_context": "whatsapp",
    "session_id": "manual_high_001"
  }'
```

Expected:
- `risk_level` should be `HIGH` or `CRITICAL`
- `requires_human_review` should be `true`
- `alert_triggered` should be `true`
- response should include an `analysis_id`
- response should include an `alert_id`

## 3. Low-risk safe analysis

```bash
curl -X POST http://localhost:8000/analyse \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Lunch was £12 each, send whenever you get a chance.",
    "platform_context": "whatsapp",
    "session_id": "manual_low_001"
  }'
```

Expected:
- `risk_level` should be `LOW` or possibly `MEDIUM`
- `alert_triggered` should be `false`
- no alert should be created unless score crosses threshold

## 4. List alerts

```bash
curl http://localhost:8000/alerts
```

Expected:
- High-risk test alert should appear.
- Alert should show simulated platform broadcast results.

## 5. Submit feedback

Replace `ANALYSIS_ID_HERE` with the `analysis_id` returned by `/analyse`.

```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": "ANALYSIS_ID_HERE",
    "session_id": "manual_high_001",
    "action": "confirm",
    "notes": "Confirmed as synthetic scam test case."
  }'
```

Other actions to test:
- `dismiss`
- `escalate`
- `override`

## 6. List feedback

```bash
curl http://localhost:8000/feedback
```

Expected:
- Recent feedback entries should be listed.

