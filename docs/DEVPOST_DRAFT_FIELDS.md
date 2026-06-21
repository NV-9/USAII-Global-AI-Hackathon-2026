# SafeGuard AI — Devpost Draft Fields

Use this as a starting point. Adjust after final frontend/backend testing.

## Tagline, max 80 characters

Cross-platform AI alerts for financial exploitation and impersonation scams.

## AI Architecture Explanation, max 600 characters

SafeGuard AI takes synthetic or user-consented message snippets plus platform context as input. An NLP classifier analyses TF-IDF text features and scam-specific behavioural signals such as urgency, secrecy, money requests, suspicious links, pressure, and impersonation markers. It outputs a risk score, risk level, confidence, triggered features, recommended action, and whether human review is required. High-risk cases trigger a simulated cross-platform alert containing risk metadata, not raw message content.

Character count: 595 including spaces.

## Human-in-the-Loop Design, max 500 characters

Our AI does not make the final decision to block, freeze, or release a payment. It only produces a risk score, explanation, and recommended action. A human operator must decide whether to confirm the case, dismiss it as a false positive, escalate it for fraud review, or allow an override. Human control is necessary because false positives can delay legitimate urgent payments and because context around personal relationships cannot be judged safely by the model alone.

Character count: 489 including spaces.

## Responsible AI Guardrail, max 500 characters

Risk: scam detection can become privacy-invasive if private messages are stored or shared. Mitigation: our prototype treats message text as transient input for scoring only. Cross-platform alerts share risk metadata, such as score, level, triggered features, and timestamp, rather than raw message content. We also use human review, explainable risk features, and feedback actions so false positives can be dismissed instead of causing permanent automated harm.

Character count: 476 including spaces.

## Data Sources, max 800 characters

We used synthetic and public/simulated data only. Synthetic scam conversations were team-generated to represent modern exploitation patterns including friend/family impersonation, fake emergency requests, crypto/investment scams, gift-card requests, phishing links, urgency, secrecy, and payment-warning bypass instructions. The NLP model documentation also lists public SMS/spam-style datasets and a team-generated synthetic scam dataset. No real private messages, confidential case files, or identifiable personal data were used. Test cases were manually labelled by expected risk level and expected behavioural features for prototype evaluation.

## Testing/Evaluation paragraph for project description

For testing, we created 40 synthetic test cases across high-risk scams, medium-risk suspicious messages, low-risk safe messages, false-positive stress cases, adversarial scam wording, feedback-loop checks, and API edge cases. These cases test whether the model detects urgency, pressure, secrecy, money requests, suspicious links, and impersonation while avoiding unnecessary alerts for legitimate financial messages. We recorded actual outputs against expected risk level, alert behaviour, human review status, and feedback handling.

## Honest limitations paragraph

The prototype demonstrates the decision-support workflow but is not a production banking or social-media integration. Cross-platform payment alerts are simulated, and the system relies on synthetic and public/simulated data rather than real private messages. The model may miss subtle adversarial scams or over-flag legitimate urgent payments. Future work would improve calibration, privacy-preserving deployment, analyst review workflows, and model drift monitoring.

