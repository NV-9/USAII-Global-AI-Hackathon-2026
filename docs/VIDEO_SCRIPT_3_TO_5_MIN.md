# SafeGuard Ai — 3 to 5 Minute Pitch Video Script

Target length: 4 minutes  
Speaker: Emmanuel or split between team members  
Replace bracketed text with actual demo details once Aaron's frontend is ready.

## 0:00–0:30 — Hook/problem

Digital exploitation is becoming harder to detect because scams no longer happen in one place. A fraudster may start by impersonating a friend or family member on social media, then push the victim to send money through a banking or payment app. The issue is not only detection. The deeper issue is fragmentation: one platform may see suspicious behaviour, while another platform has no context at all.

SafeGuard Ai addresses that gap by turning fragmented scam signals into explainable risk alerts for human review.

## 0:30–1:15 — Who it is for and scope

Our system is designed for trust and safety teams, fraud analysts, and protection-focused organisations. It is not a surveillance tool and it does not automatically freeze accounts. Instead, it gives human operators earlier warning signals so they can decide whether a case needs review, escalation, or no action.

The prototype focuses on financial coercion, impersonation scams, suspicious payment requests, urgency, secrecy, pressure, and scam links.

## 1:15–2:00 — AI approach

The NLP model analyses text messages and extracts both TF-IDF features and scam-specific behavioural features. These include urgency, pressure, money requests, suspicious links, secrecy phrases, emotional manipulation, and impersonation markers.

The model returns a structured risk assessment: a risk score, risk level, confidence score, triggered features, and whether human review is required. The backend then uses this output to decide whether a simulated cross-platform alert should be broadcast.

## 2:00–3:20 — Demo walkthrough

Now I will show the prototype working.

First, I submit a high-risk test case:  
“Send £600 now and do not tell anyone. If your bank warns you, ignore it.”

The system returns a high risk score, shows the triggered features, and recommends human review. Because the risk is high, the backend triggers a simulated alert to registered payment platforms.

Next, I show the alert record. This demonstrates the cross-platform coordination idea: the system shares risk metadata, not the full private message content.

Then I submit a safer message:  
“Lunch was £12 each, send whenever you get a chance.”

This should produce a low or lower-risk output and should not trigger a cross-platform alert. This matters because false positives can create real harm and friction.

Finally, I show the feedback loop. A human operator can confirm a true scam, dismiss a false positive, escalate a borderline case, or record an override attempt.

## 3:20–4:10 — Responsible AI tradeoff

The main responsible AI risk is privacy. Scam detection could become dangerous if it stores or exposes private messages. Our mitigation is to treat message text as transient input: it is analysed for risk, but the alert only contains risk metadata such as score, level, category, and timestamp.

Another risk is false positives. A legitimate urgent payment should not be treated as fraud automatically. That is why our system uses speed bumps, explanations, feedback, and human review rather than permanent autonomous blocking.

## 4:10–4:30 — Close/impact

SafeGuard Ai helps protection teams detect exploitation earlier, coordinate risk signals across fragmented platforms, and keep humans in control of high-stakes decisions. The prototype is not a production banking system, but it demonstrates the full decision-support workflow: signal, insight, decision, action, and feedback.

