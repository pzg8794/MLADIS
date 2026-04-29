const agentForm = document.getElementById("agent-form");
const agentLog = document.getElementById("agent-log");
const agentMessage = document.getElementById("agent-message");
const agentItem = document.getElementById("agent-item");

function csrfToken() {
  const input = document.querySelector("[name=csrfmiddlewaretoken]");
  return input ? input.value : "";
}

function appendAgentMessage(text, role) {
  const entry = document.createElement("div");
  entry.className = `agent-message ${role}`;
  entry.textContent = text;
  agentLog.appendChild(entry);
  agentLog.scrollTop = agentLog.scrollHeight;
  return entry;
}

if (agentForm) {
  agentForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = agentMessage.value.trim();
    if (!message) return;

    appendAgentMessage(message, "visitor");
    agentMessage.value = "";
    const pending = appendAgentMessage("Thinking...", "agent");

    try {
      const response = await fetch("/api/agent/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        body: JSON.stringify({
          message,
          item_id: agentItem.value || null,
          session_id: window.localStorage.getItem("mladisAgentSession") || undefined,
        }),
      });
      const json = await response.json();
      pending.remove();

      if (json.session_id) {
        window.localStorage.setItem("mladisAgentSession", json.session_id);
      }
      appendAgentMessage(json.reply || json.error || "No reply yet.", "agent");
    } catch (_error) {
      pending.remove();
      appendAgentMessage("The agent endpoint is not reachable right now.", "agent");
    }
  });
}
