async function submitTurn() {
    const statement = document.getElementById("user-statement").value;
    const actionType = document.getElementById("action-type").value;
    if (!statement) {
        alert("Please enter your argument, objection, or question.");
        return;
    }
    document.getElementById("log-content").innerHTML += `<p><strong>You [${new Date().toLocaleTimeString()}]:</strong> ${statement.replace(/\n/g, "<br>")}</p>`;
    document.getElementById("user-statement").value = "";
    document.getElementById("input-section").style.display = "none";
    document.getElementById("loading").style.display = "block";
    
    const response = await fetch("/submit_turn", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `statement=${encodeURIComponent(statement)}&action_type=${actionType}`
    });
    const data = await response.json();
    
    document.getElementById("loading").style.display = "none";
    if (data.trial_ended) {
        document.getElementById("verdict-content").innerHTML = data.verdict.replace(/\n/g, "<br>");
        document.getElementById("verdict-section").style.display = "block";
        document.getElementById("legal-help").style.display = "none";
        data.turns.forEach(turn => {
            document.getElementById("log-content").innerHTML += `<p><strong>${turn.role} [${turn.timestamp}]:</strong> ${turn.statement.replace(/\n/g, "<br>")}</p>`;
        });
    } else {
        data.turns.forEach(turn => {
            document.getElementById("log-content").innerHTML += `<p><strong>${turn.role} [${turn.timestamp}]:</strong> ${turn.statement.replace(/\n/g, "<br>")}</p>`;
        });
        document.getElementById("help-content").innerHTML = data.legal_help.replace(/\n/g, "<br>");
        document.getElementById("witness-content").innerHTML = data.witnesses.join("<br><br>");
        document.getElementById("current-round").textContent = data.current_round;
        document.getElementById("input-section").style.display = "block";
    }
    document.getElementById("log-content").scrollTop = document.getElementById("log-content").scrollHeight;
}

function toggleHelp() {
    const helpBox = document.getElementById("legal-help");
    helpBox.classList.toggle("hidden");
}