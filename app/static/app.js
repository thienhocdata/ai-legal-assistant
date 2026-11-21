const form = document.querySelector("#chat-form");
const input = document.querySelector("#question");
const submit = document.querySelector("#submit");
const messages = document.querySelector("#messages");
const suggestionButtons = Array.from(document.querySelectorAll(".suggestions button"));
const REQUEST_TIMEOUT_MS = 90000;
let requestPending = false;
let nextRequestId = 0;
// This is deliberately tab-memory only. Only the server may propose the next
// bounded clarification context; displayed conversation HTML is never history.
let continuationContext = null;
// Completed turns only, held in this tab's memory. Never read the rendered DOM
// as history or persist conversations in browser/server storage.
let conversationHistory = [];
const HISTORY_MAX_MESSAGES = 8;
const HISTORY_MAX_MESSAGE_CHARS = 4000;
const HISTORY_MAX_TOTAL_CHARS = 12000;

const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
}[char]));

function addUserMessage(text) {
  messages.insertAdjacentHTML("beforeend", `<article class="message user"><div class="bubble"><p>${escapeHtml(text)}</p></div></article>`);
  messages.scrollTop = messages.scrollHeight;
}

function addLoading(requestId) {
  const loadingId = `loading-${requestId}`;
  messages.insertAdjacentHTML("beforeend", `<article id="${loadingId}" class="message assistant loading"><div class="avatar">ML</div><div class="bubble"><p>Đang xử lý câu hỏi</p></div></article>`);
  messages.scrollTop = messages.scrollHeight;
  return loadingId;
}

function renderResponse(data) {
  const clarification = (data.clarification_questions || []).map((q) => `<p>• ${escapeHtml(q)}</p>`).join("");
  const citations = (data.citations || []).map((item) => `<details class="citation"><summary><strong>${escapeHtml(item.citation_id)} Điều ${item.article_no}</strong> · ${escapeHtml(item.article_title)}</summary><p>${escapeHtml(item.quote || "Không có đoạn trích.")}</p></details>`).join("");
  const modeLabel = data.generation_fallback_reason
    ? (data.provider === "extractive"
      ? "Lượt này chưa tổng hợp được câu trả lời; mình gửi các đoạn luật để bạn đối chiếu."
      : "Lượt này chưa kết nối được mô hình trò chuyện, mình dùng phản hồi có sẵn.")
    : data.provider === "extractive" && data.answer_kind !== "source_definition"
    ? "Các đoạn trích được giữ nguyên từ nguồn luật."
    : (data.provider && data.citations?.length && !["extractive", "glossary"].includes(data.provider)
      ? "Câu trả lời được mô hình tổng hợp từ các căn cứ bên dưới." : "");
  const provider = modeLabel ? `<p class="response-meta">${modeLabel}</p>` : "";
  const disclaimer = data.disclaimer ? `<p class="response-meta">${escapeHtml(data.disclaimer)}</p>` : "";
  messages.insertAdjacentHTML("beforeend", `<article class="message assistant"><div class="avatar">ML</div><div class="bubble"><p>${escapeHtml(data.answer || "Không có câu trả lời.").replace(/\n/g, "<br>")}</p>${clarification}<div class="citation-list">${citations}</div>${provider}${disclaimer}</div></article>`);
  messages.scrollTop = messages.scrollHeight;
}

function setPending(value) {
  requestPending = value;
  submit.disabled = value;
  suggestionButtons.forEach((button) => { button.disabled = value; });
  form.setAttribute("aria-busy", String(value));
}

function readContinuationContext(data) {
  const pendingFeedback = data.status === "smalltalk"
    && ["feedback_tone", "feedback_relevance", "rephrase_request", "acknowledgement", "conversation_capability"].includes(data.conversation_intent);
  if (!["needs_clarification", "insufficient_coverage"].includes(data.status) && !pendingFeedback) return null;
  const context = data.continuation_context;
  if (!context || typeof context.question !== "string" || !Array.isArray(context.answers)) return null;
  if (!context.question.trim() || context.question.length > 2000 || context.answers.length > 3) return null;
  if (context.answers.some((answer) => typeof answer !== "string" || !answer.trim() || answer.length > 2000)) return null;
  return { question: context.question, answers: [...context.answers] };
}

function rememberCompletedTurn(question, data) {
  // A blocked/rejected request must not poison later prompts. Retain only a
  // completed response with actual text, not a client-generated error bubble.
  if (["blocked", "generation_rejected"].includes(data.status)
      || typeof data.answer !== "string" || !data.answer.trim()) return;
  const turns = [{ role: "user", content: question }];
  const responseText = data.answer.trim();
  // Retain complete messages only. A long source quote is omitted from history
  // rather than clipped, while the latest question remains available.
  if (responseText.length <= HISTORY_MAX_MESSAGE_CHARS) {
    turns.push({ role: "assistant", content: responseText });
  }
  conversationHistory.push(...turns);
  const totalChars = () => conversationHistory.reduce((sum, turn) => sum + turn.content.length, 0);
  while (conversationHistory.length > HISTORY_MAX_MESSAGES || totalChars() > HISTORY_MAX_TOTAL_CHARS) {
    conversationHistory.shift();
    // Do not leave an older assistant response without its preceding question.
    if (conversationHistory[0]?.role === "assistant") conversationHistory.shift();
  }
}

async function ask(question, { startNewTopic = false } = {}) {
  question = String(question || "").trim();
  // The guard must run before adding a message, clearing context or starting a
  // request: suggestion clicks and programmatic submit can otherwise overlap.
  if (requestPending || !question) return false;
  startNewTopic = startNewTopic || /^(?:câu hỏi mới|cau hoi moi):/i.test(question);
  if (startNewTopic) {
    continuationContext = null;
    conversationHistory = [];
  }
  setPending(true);
  const requestId = ++nextRequestId;
  const controller = new AbortController();
  let timedOut = false;
  const timeoutId = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, REQUEST_TIMEOUT_MS);
  const payload = { question };
  if (conversationHistory.length) {
    payload.conversation_history = conversationHistory.map((turn) => ({ ...turn }));
  }
  if (continuationContext && !startNewTopic) {
    payload.clarification_context = {
      question: continuationContext.question,
      answers: [...continuationContext.answers]
    };
  }
  addUserMessage(question);
  const loadingId = addLoading(requestId);
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal
    });
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "Không thể xử lý câu hỏi.");
    if (!data || typeof data !== "object" || Array.isArray(data)) throw new Error("Phản hồi không hợp lệ. Bạn có thể gửi lại câu hỏi.");
    renderResponse(data);
    continuationContext = readContinuationContext(data);
    rememberCompletedTurn(question, data);
    return true;
  } catch (error) {
    const message = timedOut
      ? "Yêu cầu quá 90 giây. Bạn có thể thử gửi lại."
      : (error?.name === "AbortError" ? "Yêu cầu đã bị hủy. Bạn có thể gửi lại." : (error?.message || "Không thể kết nối dịch vụ."));
    renderResponse({ answer: message, citations: [] });
    // Retain the context that preceded this request; a failed request must not
    // become a successful conversation turn. Preserve any new draft as well.
    if (!input.value.trim()) input.value = question;
    return false;
  } finally {
    clearTimeout(timeoutId);
    document.querySelector(`#${loadingId}`)?.remove();
    setPending(false);
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  if (requestPending) return false;
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  return ask(question);
});

suggestionButtons.forEach((button) => {
  button.addEventListener("click", () => ask(button.textContent.trim(), { startNewTopic: true }));
});

async function checkHealth(attempt = 0) {
  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    if (!response.ok) throw new Error("health check failed");
    const data = await response.json();
    const ready = data.status === "ready" && data.runtime?.ready === true;
    document.querySelector("#status-dot").classList.toggle("ready", ready);
    document.querySelector("#status-text").textContent = ready
      ? "Kho tri thức sẵn sàng"
      : (data.status === "warming_up" ? "Đang nạp kho tri thức" : "Kho tri thức chưa sẵn sàng");
    if (!ready && ["warming_up", "degraded"].includes(data.status)) {
      if (attempt < 29) setTimeout(() => checkHealth(attempt + 1), 2000);
      else document.querySelector("#status-text").textContent = "Kho tri thức chưa sẵn sàng. Hãy tải lại sau.";
    }
  } catch (_) {
    document.querySelector("#status-dot").classList.toggle("ready", false);
    document.querySelector("#status-text").textContent = "Không kết nối được dịch vụ";
  }
}

checkHealth();
