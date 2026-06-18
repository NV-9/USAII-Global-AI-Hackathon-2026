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

        if (data.risk_score > 90) {

            document.getElementById("escalationPanel").style.display =
                "block";

            document.getElementById("referenceNumber").textContent =
                crypto.randomUUID()
                    .substring(0, 8)
                    .toUpperCase();

        }
        if (data.risk_level !== "LOW") {
    startCoolingTimer(30);
    }
        loadAlerts();
    } catch (err) {
        console.error(err);
        alert("Analysis failed.");
    }
}


async function dismissAlert() {
    if (!currentAnalysisId) return;

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
}

async function loadAlerts() {
    try {
        const response = await fetch(`${API_BASE}/alerts?limit=5`);
        const data = await response.json();

        const container = document.getElementById("alertsList");

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

function cancelAction() {
    alert("Action cancelled.");
}

function proceedAnyway() {
    alert("Proceeding despite warning.");
}
document.addEventListener("DOMContentLoaded", loadAlerts);
