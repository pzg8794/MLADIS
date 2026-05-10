function csrfToken(panel) {
  const input = panel.querySelector("[name=csrfmiddlewaretoken]") || document.querySelector("[name=csrfmiddlewaretoken]");
  return input ? input.value : "";
}

function appendAgentMessage(log, text, role) {
  const empty = log.querySelector(".agent-empty");
  if (empty) empty.remove();
  const entry = document.createElement("div");
  entry.className = `agent-message ${role}`;
  entry.textContent = text;
  log.appendChild(entry);
  log.scrollTop = log.scrollHeight;
  return entry;
}

document.querySelectorAll("[data-agent-panel]").forEach((panel) => {
  const form = panel.querySelector(".agent-form");
  const log = panel.querySelector(".agent-log");
  const messageInput = panel.querySelector(".agent-message");
  const itemSelect = panel.querySelector(".agent-item");

  if (!form || !log || !messageInput) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = messageInput.value.trim();
    if (!message) return;

    appendAgentMessage(log, message, "visitor");
    messageInput.value = "";
    const pending = appendAgentMessage(log, "Thinking...", "agent");

    try {
      const response = await fetch("/api/agent/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(panel),
        },
        body: JSON.stringify({
          message,
          item_id: itemSelect && itemSelect.value ? itemSelect.value : null,
          session_id: window.localStorage.getItem("mladisAgentSession") || undefined,
        }),
      });
      const json = await response.json();
      pending.remove();

      if (json.session_id) {
        window.localStorage.setItem("mladisAgentSession", json.session_id);
      }
      appendAgentMessage(log, json.reply || json.error || "No reply yet.", "agent");
    } catch (_error) {
      pending.remove();
      appendAgentMessage(log, "The agent endpoint is not reachable right now.", "agent");
    }
  });
});
