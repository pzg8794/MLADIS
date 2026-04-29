const chat = document.getElementById("chat");
const form = document.getElementById("form");
const input = document.getElementById("input");

function addMsg(text, who) {
  const empty = chat.querySelector(".empty");
  if (empty) {
    empty.remove();
  }

  const div = document.createElement("div");
  div.className = `msg ${who}`;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = input.value.trim();
  if (!message) {
    input.focus();
    return;
  }

  addMsg(message, "me");
  input.value = "";
  const pending = addMsg("Thinking...", "bot");

  try {
    const response = await fetch("/api/agent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const json = await response.json();

    pending.remove();
    addMsg(json.reply || json.error || "No reply", "bot");
  } catch (error) {
    pending.remove();
    addMsg("Error calling agent API", "bot");
  }
});
