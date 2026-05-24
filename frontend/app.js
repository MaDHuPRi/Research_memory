const API = "http://127.0.0.1:8080/api";

const messagesEl = document.getElementById("messages");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const sessionIdEl = document.getElementById("sessionId");
const memoryQueryEl = document.getElementById("memoryQuery");
const searchBtn = document.getElementById("searchBtn");
const memoryResultsEl = document.getElementById("memoryResults");
const loadMemoryBtn = document.getElementById("loadMemoryBtn");
const memoryLogEl = document.getElementById("memoryLog");

// ── Auto-resize textarea ──
userInput.addEventListener("input", () => {
  userInput.style.height = "auto";
  userInput.style.height = Math.min(userInput.scrollHeight, 140) + "px";
});

// ── Send on Enter (Shift+Enter for newline) ──
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendBtn.addEventListener("click", sendMessage);
searchBtn.addEventListener("click", searchMemory);
loadMemoryBtn.addEventListener("click", loadMemoryLog);

memoryQueryEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter") searchMemory();
});

// ── Chat ──
async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  const sessionId = sessionIdEl.value.trim() || "default";

  appendMessage("user", message);
  userInput.value = "";
  userInput.style.height = "auto";

  const thinkingEl = appendThinking();
  sendBtn.disabled = true;

  try {
    const res = await fetch(`${API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId })
    });
    const data = await res.json();
    thinkingEl.remove();
    appendMessage("assistant", data.response);
  } catch (err) {
    thinkingEl.remove();
    appendMessage("assistant", "⚠ Could not reach the server. Make sure Flask is running on port 5000.");
  } finally {
    sendBtn.disabled = false;
    userInput.focus();
  }
}

function appendMessage(role, text) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.innerHTML = `
    <div class="bubble">${escapeHtml(text)}</div>
    <div class="meta">${role === "user" ? "You" : "ResearchBot"} · ${timestamp()}</div>
  `;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

function appendThinking() {
  const div = document.createElement("div");
  div.className = "message assistant thinking";
  div.innerHTML = `<div class="bubble">Thinking</div>`;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

// ── Memory search ──
async function searchMemory() {
  const query = memoryQueryEl.value.trim();
  const sessionId = sessionIdEl.value.trim() || "default";
  if (!query) return;

  memoryResultsEl.innerHTML = `<div class="memory-item">Searching...</div>`;
  try {
    const res = await fetch(`${API}/memory/search?q=${encodeURIComponent(query)}&session_id=${sessionId}`);
    const data = await res.json();
    renderMemoryItems(memoryResultsEl, data.results);
  } catch {
    memoryResultsEl.innerHTML = `<div class="memory-item">⚠ Search failed.</div>`;
  }
}

async function loadMemoryLog() {
  const sessionId = sessionIdEl.value.trim() || "default";
  memoryLogEl.innerHTML = `<div class="memory-item">Loading...</div>`;
  try {
    const res = await fetch(`${API}/memory/all?session_id=${sessionId}`);
    const data = await res.json();
    renderMemoryItems(memoryLogEl, data.memories);
  } catch {
    memoryLogEl.innerHTML = `<div class="memory-item">⚠ Failed to load.</div>`;
  }
}

function renderMemoryItems(container, items) {
  if (!items || items.length === 0) {
    container.innerHTML = `<div class="memory-item">No memories found.</div>`;
    return;
  }
  container.innerHTML = items.map(m => {
    const rel = m.relevance !== undefined ? `<div class="relevance">relevance ${m.relevance}</div>` : "";
    const date = (m.metadata?.timestamp || "").slice(0, 10);
    return `
      <div class="memory-item">
        ${rel}
        <div>${escapeHtml(m.content)}</div>
        ${date ? `<div class="relevance">${date}</div>` : ""}
      </div>
    `;
  }).join("");
}

// ── Helpers ──
function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>");
}

function timestamp() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
