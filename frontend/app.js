const API_BASE = "http://localhost:8000";
console.log("APP JS LOADED");
let currentAnalysisId = null;
const sessionId = crypto.randomUUID();

async function analyseMessage() {
    const message = document.getElementById("msgInput").value.trim();

    if (!message) {
        alert("Enter a message first.");
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/analyse`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message,
                session_id: sessionId
            })
        });

        const data = await response.json();

        currentAnalysisId = data.analysis_id;

        const result = document.getElementById("result");
        result.style.display = "block";

        document.getElementById("riskLabel").textContent =
            data.risk_level;

        document.getElementById("riskScore").textContent =
            `Score: ${data.risk_score}/100`;

        document.getElementById("resultWhy").textContent =
            data.recommended_action;

        document.getElementById("resultTags").innerHTML =
            data.triggered_features
                .map(f => `<span class="tag">${f}</span>`)
                .join("");
        result.className =
            `result ${data.risk_level.toLowerCase()}`;

        document.getElementById("decisionPanel").style.display = "none";
        document.getElementById("escalationPanel").style.display = "none";

        if (data.escalation_triggered || data.override_locked) {
            showEscalationPanel(data.escalation_id);
        } else if (data.risk_level !== "LOW") {
            startCoolingTimer(30);
        }
        loadAlerts();
    } catch (err) {
        console.error(err);
        alert("Analysis failed.");
    }
}


async function loadAlerts() {
    const container = document.getElementById("alertsList");
    if (!container) return;

    try {
        const response = await fetch(`${API_BASE}/alerts?limit=5`);
        const data = await response.json();

        if (!data.alerts || data.alerts.length === 0) {
            container.innerHTML =
                "<p>No alerts available.</p>";
            return;
        }

        container.innerHTML = data.alerts.map(alert => `
            <div class="alert-item">
                <div class="alert-dot ${alert.risk_level.toLowerCase()}"></div>
                <span>
                    ${alert.risk_level} Risk
                    (Score: ${alert.risk_score})
                </span>
            </div>
        `).join("");

    } catch (err) {
        console.error(err);
    }
}
function showEscalationPanel(escalationId) {
    document.getElementById("decisionPanel").style.display = "none";

    const panel = document.getElementById("escalationPanel");
    panel.style.display = "block";

    document.getElementById("referenceNumber").textContent =
        escalationId || "Pending";
}

function startCoolingTimer(seconds = 30) {

    const panel = document.getElementById("decisionPanel");
    const timerLabel = document.getElementById("coolingTimer");
    const proceedBtn = document.getElementById("proceedBtn");

    panel.style.display = "block";
    proceedBtn.disabled = true;

    let remaining = seconds;

    timerLabel.textContent = remaining;

    const timer = setInterval(() => {

        remaining--;

        timerLabel.textContent = remaining;

        if (remaining <= 0) {
            clearInterval(timer);
            proceedBtn.disabled = false;
        }

    }, 1000);
}

async function cancelAction() {
    if (!currentAnalysisId) return;

    try {
        await fetch(`${API_BASE}/feedback`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                analysis_id: currentAnalysisId,
                session_id: sessionId,
                action: "dismiss"
            })
        });

        document.getElementById("result").style.display = "none";

    } catch (err) {
        console.error(err);
        alert("Failed to submit cancellation.");
    }
}

async function proceedAnyway() {
    if (!currentAnalysisId) return;

    try {
        const response = await fetch(`${API_BASE}/feedback`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                analysis_id: currentAnalysisId,
                session_id: sessionId,
                action: "override"
            })
        });

        if (response.status === 403) {
            alert(
                "This payment has been escalated to a fraud analyst and cannot be overridden."
            );
            return;
        }

        alert("User chose to proceed despite the warning.");

    } catch (err) {
        console.error(err);
        alert("Failed to submit override.");
    }
}
async function loadEscalations() {
    const container = document.getElementById("escalationsList");
    if (!container) return;

    try {
        const response = await fetch(`${API_BASE}/escalations?pending_only=true`);
        const data = await response.json();

        if (!data.escalations || data.escalations.length === 0) {
            container.innerHTML = "<p>No pending escalations.</p>";
            return;
        }

        container.innerHTML = data.escalations.map(esc => `
            <div class="escalation-item" id="esc-${esc.escalation_id}">
                <div class="escalation-row">
                    <span class="risk-score">Score: ${esc.risk_score}/100</span>
                    <span class="escalation-id">${esc.escalation_id}</span>
                </div>
                <p class="subtitle">${esc.reason}</p>
                <div class="override-row">
                    <button class="btn-override btn-confirm" onclick="resolveEscalation('${esc.escalation_id}', 'confirmed_fraud')">
                        Confirm Fraud
                    </button>
                    <button class="btn-override btn-dismiss" onclick="resolveEscalation('${esc.escalation_id}', 'released')">
                        Release (False Positive)
                    </button>
                </div>
            </div>
        `).join("");

    } catch (err) {
        console.error(err);
        container.innerHTML = "<p>Failed to load escalations.</p>";
    }
}

async function resolveEscalation(escalationId, resolution) {
    try {
        const response = await fetch(`${API_BASE}/escalations/${escalationId}/resolve`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ resolution })
        });

        if (!response.ok) {
            alert("Failed to resolve escalation.");
            return;
        }

        loadEscalations();

    } catch (err) {
        console.error(err);
        alert("Failed to resolve escalation.");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadAlerts();
    loadEscalations();
});
