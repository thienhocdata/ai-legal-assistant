const form = document.querySelector("#chat-form");
const input = document.querySelector("#question");
const submit = document.querySelector("#submit");
const messages = document.querySelector("#messages");

const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
}[char]));

function addUserMessage(text) {
  messages.insertAdjacentHTML("beforeend", `<article class="message user"><div class="bubble"><p>${escapeHtml(text)}</p></div></article>`);
  messages.scrollTop = messages.scrollHeight;
}

function addLoading() {
  messages.insertAdjacentHTML("beforeend", `<article id="loading" class="message assistant loading"><div class="avatar">ML</div><div class="bubble"><p>Đang đối chiếu căn cứ</p></div></article>`);
  messages.scrollTop = messages.scrollHeight;
}

function renderResponse(data) {
  document.querySelector("#loading")?.remove();
  const clarification = (data.clarification_questions || []).map((q) => `<p>• ${escapeHtml(q)}</p>`).join("");
  const citations = (data.citations || []).map((item) => `<details class="citation"><summary><strong>${escapeHtml(item.citation_id)} Điều ${item.article_no}</strong> · ${escapeHtml(item.article_title)}</summary><p>${escapeHtml(item.quote || "Không có đoạn trích.")}</p></details>`).join("");
  const provider = data.provider ? `<p class="response-meta">Chế độ trả lời: ${escapeHtml(data.provider)} · ${escapeHtml(data.model || "")}</p>` : "";
  const disclaimer = data.disclaimer ? `<p class="response-meta">${escapeHtml(data.disclaimer)}</p>` : "";
  messages.insertAdjacentHTML("beforeend", `<article class="message assistant"><div class="avatar">ML</div><div class="bubble"><p>${escapeHtml(data.answer || "Không có câu trả lời.").replace(/\n/g, "<br>")}</p>${clarification}<div class="citation-list">${citations}</div>${provider}${disclaimer}</div></article>`);
  messages.scrollTop = messages.scrollHeight;
}

async function ask(question) {
  addUserMessage(question);
  addLoading();
  submit.disabled = true;
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Không thể xử lý câu hỏi.");
    renderResponse(data);
  } catch (error) {
    renderResponse({ answer: error.message, citations: [] });
  } finally {
    submit.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  ask(question);
});

document.querySelectorAll(".suggestions button").forEach((button) => {
  button.addEventListener("click", () => ask(button.textContent.trim()));
});

fetch("/api/health").then((response) => response.json()).then((data) => {
  const ready = data.status === "ready";
  document.querySelector("#status-dot").classList.toggle("ready", ready);
  document.querySelector("#status-text").textContent = ready ? "Kho tri thức sẵn sàng" : "Hệ thống chưa đủ dữ liệu";
}).catch(() => {
  document.querySelector("#status-text").textContent = "Không kết nối được dịch vụ";
});
