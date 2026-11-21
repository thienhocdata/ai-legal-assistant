const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "../app/static/app.js"), "utf8");
const flush = () => new Promise(setImmediate);

function createPage({ healthResponses = [{ status: "ready", runtime: { ready: true } }] } = {}) {
  const nodes = new Map();
  const fragments = [];
  const timers = new Map();
  const requests = [];
  let timerSequence = 0;
  let activeRequests = 0;
  let maxActiveRequests = 0;
  let healthCalls = 0;

  class Element {
    constructor(id) {
      this.id = id;
      this.value = "";
      this.textContent = "";
      this.disabled = false;
      this.listeners = new Map();
      this.attributes = {};
      this.classes = new Set();
      this.classList = { toggle: (name, enabled) => enabled ? this.classes.add(name) : this.classes.delete(name) };
    }
    addEventListener(type, callback) { this.listeners.set(type, callback); }
    emit(type) { return this.listeners.get(type)?.({ preventDefault() {} }); }
    setAttribute(name, value) { this.attributes[name] = value; }
    focus() { this.focused = true; }
    insertAdjacentHTML(_, html) {
      const fragment = { html, removed: false };
      fragments.push(fragment);
      const id = /id="([^"]+)"/.exec(html)?.[1];
      if (id) {
        const element = new Element(id);
        element.remove = () => { fragment.removed = true; nodes.delete(`#${id}`); };
        nodes.set(`#${id}`, element);
      }
      this.scrollHeight = fragments.length * 100;
    }
  }

  for (const id of ["chat-form", "question", "submit", "messages", "status-dot", "status-text"]) {
    nodes.set(`#${id}`, new Element(id));
  }
  const suggestions = ["Điều kiện chuyển nhượng đất?", "Cấp sổ đỏ thế nào?", "Hòa giải đất ở đâu?"]
    .map((label, index) => Object.assign(new Element(`suggestion-${index}`), { textContent: label }));
  const fetch = (url, init) => {
    if (url === "/api/health") {
      const data = healthResponses[Math.min(healthCalls++, healthResponses.length - 1)];
      return Promise.resolve({ ok: true, json: () => Promise.resolve(data) });
    }
    assert.equal(url, "/api/chat");
    activeRequests += 1;
    maxActiveRequests = Math.max(maxActiveRequests, activeRequests);
    let resolvePromise;
    let rejectPromise;
    let settled = false;
    const promise = new Promise((resolve, reject) => { resolvePromise = resolve; rejectPromise = reject; });
    const finish = () => { if (settled) return false; settled = true; activeRequests -= 1; return true; };
    const request = {
      payload: JSON.parse(init.body), signal: init.signal,
      resolve(data, { ok = true } = {}) {
        if (finish()) resolvePromise({ ok, json: () => Promise.resolve(data) });
      },
      reject(error = new Error("Network unavailable")) { if (finish()) rejectPromise(error); }
    };
    init.signal.addEventListener("abort", () => {
      const error = new Error("aborted");
      error.name = "AbortError";
      request.reject(error);
    });
    requests.push(request);
    return promise;
  };
  const sandbox = {
    document: { querySelector: (selector) => nodes.get(selector), querySelectorAll: () => suggestions },
    fetch, AbortController,
    setTimeout(callback, delay) { const id = ++timerSequence; timers.set(id, { callback, delay }); return id; },
    clearTimeout(id) { timers.delete(id); }
  };
  for (const storage of ["localStorage", "sessionStorage"]) {
    Object.defineProperty(sandbox, storage, { get() { throw new Error(`Unexpected ${storage} access`); } });
  }
  vm.runInNewContext(source, sandbox, { filename: "app.js" });
  const input = nodes.get("#question");
  return {
    nodes, suggestions, fragments, timers, requests, input,
    submit(question) { input.value = question; return nodes.get("#chat-form").emit("submit"); },
    controlsDisabled() { return nodes.get("#submit").disabled && suggestions.every((button) => button.disabled); },
    html() { return fragments.filter((fragment) => !fragment.removed).map((fragment) => fragment.html).join("\n"); },
    loadingIds() { return [...nodes.keys()].filter((key) => key.startsWith("#loading-")); },
    fireTimer(delay) {
      const entry = [...timers].find(([, timer]) => timer.delay === delay);
      assert.ok(entry, `Expected a ${delay}ms timer`);
      timers.delete(entry[0]);
      return entry[1].callback();
    },
    get maxActiveRequests() { return maxActiveRequests; },
    get healthCalls() { return healthCalls; }
  };
}

function answer(text = "Căn cứ [1]", status = "success") {
  return { status, answer: text, citations: [] };
}

test("suggestion and programmatic submit cannot overlap or reorder responses", async () => {
  const page = createPage();
  const first = page.suggestions[0].emit("click");
  assert.equal(page.requests.length, 1);
  assert.equal(page.controlsDisabled(), true);
  assert.deepEqual(page.loadingIds(), ["#loading-1"]);
  assert.equal(await page.suggestions[1].emit("click"), false);
  page.input.value = "Bản nháp mới";
  assert.equal(await page.nodes.get("#chat-form").emit("submit"), false);
  assert.equal(page.input.value, "Bản nháp mới");
  assert.equal(page.requests.length, 1);
  assert.equal(page.fragments.filter((row) => row.html.includes('class="message user"')).length, 1);
  page.requests[0].resolve(answer("first answer"));
  assert.equal(await first, true);
  assert.deepEqual(page.loadingIds(), []);
  assert.equal(page.controlsDisabled(), false);
  const second = page.suggestions[1].emit("click");
  assert.deepEqual(page.loadingIds(), ["#loading-2"]);
  page.requests[1].resolve(answer("second answer"));
  await second;
  assert.equal(page.maxActiveRequests, 1);
  assert.ok(page.html().indexOf("first answer") < page.html().indexOf("second answer"));
});

test("uses only bounded server continuation context without duplicating current reply", async () => {
  const page = createPage();
  const original = "Thu hồi đất được bồi thường bao nhiêu?";
  let pending = page.submit(original);
  assert.deepEqual(page.requests[0].payload, { question: original });
  page.requests[0].resolve({ ...answer("Địa phương nào?", "needs_clarification"),
    continuation_context: { question: original, answers: [] } });
  await pending;
  pending = page.submit("Đồng Nai");
  assert.deepEqual(page.requests[1].payload, {
    question: "Đồng Nai", clarification_context: { question: original, answers: [] },
    conversation_history: [
      { role: "user", content: original }, { role: "assistant", content: "Địa phương nào?" }
    ]
  });
  page.requests[1].resolve({ ...answer("Bạn cần thêm nguồn địa phương", "insufficient_coverage"),
    continuation_context: { question: original, answers: ["Đồng Nai"] } });
  await pending;
  pending = page.submit("Đất trồng lúa");
  assert.deepEqual(page.requests[2].payload, {
    question: "Đất trồng lúa", clarification_context: { question: original, answers: ["Đồng Nai"] },
    conversation_history: [
      { role: "user", content: original }, { role: "assistant", content: "Địa phương nào?" },
      { role: "user", content: "Đồng Nai" }, { role: "assistant", content: "Bạn cần thêm nguồn địa phương" }
    ]
  });
  page.requests[2].resolve(answer());
  await pending;
  pending = page.submit("Điều kiện chuyển nhượng đất?");
  assert.equal("clarification_context" in page.requests[3].payload, false);
  page.requests[3].resolve(answer());
  await pending;
});

test("new-topic suggestions omit pending clarification context", async () => {
  const page = createPage();
  let pending = page.submit("Câu hỏi đang cần làm rõ về đất");
  page.requests[0].resolve({ ...answer("Cần làm rõ", "needs_clarification"),
    continuation_context: { question: "Câu hỏi đang cần làm rõ về đất", answers: [] } });
  await pending;
  pending = page.suggestions[0].emit("click");
  assert.equal("clarification_context" in page.requests[1].payload, false);
  assert.equal("conversation_history" in page.requests[1].payload, false);
  page.requests[1].resolve(answer());
  await pending;
});

test("feedback preserves pending clarification without appending a case fact", async () => {
  const page = createPage();
  const context = { question: "Tôi chuyển đất được không?", answers: [] };
  let pending = page.submit(context.question);
  page.requests[0].resolve({ ...answer("Cần làm rõ", "needs_clarification"), continuation_context: context });
  await pending;
  pending = page.submit("Mình chưa hiểu");
  page.requests[1].resolve({ ...answer("Bạn muốn làm rõ phần nào?", "smalltalk"),
    conversation_intent: "rephrase_request", continuation_context: context });
  await pending;
  pending = page.submit("Chuyển mục đích sử dụng đất");
  assert.deepEqual(page.requests[2].payload, {
    question: "Chuyển mục đích sử dụng đất", clarification_context: context,
    conversation_history: [
      { role: "user", content: context.question }, { role: "assistant", content: "Cần làm rõ" },
      { role: "user", content: "Mình chưa hiểu" }, { role: "assistant", content: "Bạn muốn làm rõ phần nào?" }
    ]
  });
  page.requests[2].resolve(answer());
  await pending;
});

test("an API fallback is disclosed without displaying internal error details", async () => {
  const page = createPage();
  const pending = page.submit("Điều kiện chuyển nhượng đất?");
  page.requests[0].resolve({ ...answer("Căn cứ để đối chiếu [1]"),
    provider: "extractive", generation_fallback_reason: "ProviderRequestError" });
  await pending;
  assert.match(page.html(), /Lượt này chưa tổng hợp được câu trả lời/);
  assert.doesNotMatch(page.html(), /ProviderRequestError/);
  assert.doesNotMatch(page.html(), /Câu trả lời được mô hình tổng hợp/);
});

test("nonlegal hosted conversation does not claim to have cited legal evidence", async () => {
  const page = createPage();
  const pending = page.submit("Bạn có trò chuyện được không?");
  page.requests[0].resolve({ ...answer("Bạn cứ nhắn điều muốn trao đổi nhé.", "smalltalk"),
    provider: "qwen", conversation_mode: "hosted" });
  await pending;
  assert.match(page.html(), /Bạn cứ nhắn/);
  assert.doesNotMatch(page.html(), /tổng hợp từ các căn cứ/);
});

test("terminal statuses clear context even if a response includes a context-shaped value", async () => {
  for (const status of ["success", "smalltalk", "out_of_scope", "blocked", "generation_rejected"]) {
    const page = createPage();
    let pending = page.submit("Hỏi về đất");
    page.requests[0].resolve({ ...answer("Làm rõ", "needs_clarification"),
      continuation_context: { question: "Hỏi về đất", answers: [] } });
    await pending;
    pending = page.submit("Bổ sung");
    page.requests[1].resolve({ ...answer("Kết quả", status),
      continuation_context: { question: "Không được giữ", answers: [] } });
    await pending;
    pending = page.submit("Câu mới về đất");
    assert.equal("clarification_context" in page.requests[2].payload, false);
    page.requests[2].resolve(answer());
    await pending;
  }
});

test("network failure restores failed input and preserves pre-request context", async () => {
  const page = createPage();
  let pending = page.submit("Thu hồi đất thế nào?");
  page.requests[0].resolve({ ...answer("Làm rõ", "needs_clarification"),
    continuation_context: { question: "Thu hồi đất thế nào?", answers: [] } });
  await pending;
  pending = page.submit("Đồng Nai");
  page.requests[1].reject();
  assert.equal(await pending, false);
  assert.equal(page.input.value, "Đồng Nai");
  assert.equal(page.controlsDisabled(), false);
  assert.deepEqual(page.loadingIds(), []);
  pending = page.submit(page.input.value);
  assert.deepEqual(page.requests[2].payload, page.requests[1].payload);
  page.requests[2].resolve(answer());
  await pending;
});

test("request failure does not overwrite a new draft typed while waiting", async () => {
  const page = createPage();
  const pending = page.submit("Câu hỏi cần gửi");
  page.input.value = "Bản nháp mới cần giữ";
  page.requests[0].reject();
  await pending;
  assert.equal(page.input.value, "Bản nháp mới cần giữ");
});

test("history sends completed prior turns only and keeps response text separate from HTML", async () => {
  const page = createPage();
  let pending = page.submit("Câu đầu");
  assert.equal("conversation_history" in page.requests[0].payload, false);
  page.requests[0].resolve(answer("Một câu <b>nguyên văn</b>."));
  await pending;
  pending = page.submit("Giải thích thêm nhé");
  assert.deepEqual(page.requests[1].payload.conversation_history, [
    { role: "user", content: "Câu đầu" },
    { role: "assistant", content: "Một câu <b>nguyên văn</b>." }
  ]);
  assert.equal(page.requests[1].payload.conversation_history.some((turn) => turn.content === "Giải thích thêm nhé"), false);
  assert.match(page.html(), /&lt;b&gt;nguyên văn&lt;\/b&gt;/);
  page.requests[1].resolve(answer());
  await pending;
});

test("long source replies are omitted whole while retaining their question", async () => {
  const page = createPage();
  const longSource = "Điều kiện và ngoại lệ cần giữ nguyên. ".repeat(150);
  assert.ok(longSource.length > 4000);
  let pending = page.submit("Câu hỏi có nguồn dài");
  page.requests[0].resolve(answer(longSource));
  await pending;
  pending = page.submit("Nói gọn lại giúp mình");
  assert.deepEqual(page.requests[1].payload.conversation_history, [
    { role: "user", content: "Câu hỏi có nguồn dài" }
  ]);
  assert.ok(page.html().includes(longSource));
  page.requests[1].resolve(answer());
  await pending;
});

test("history evicts old complete turns to obey message and total budgets", async () => {
  for (const responseChars of [20, 3500]) {
    const page = createPage();
    for (let index = 0; index < 6; index += 1) {
      const pending = page.submit(`Câu ${index}`);
      page.requests[index].resolve(answer(`${index}`.repeat(responseChars)));
      await pending;
    }
    const pending = page.submit("Câu tiếp theo");
    const history = page.requests[6].payload.conversation_history;
    assert.ok(history.length <= 8);
    assert.ok(history.reduce((sum, turn) => sum + turn.content.length, 0) <= 12000);
    assert.ok(history.every((turn) => turn.content.length <= 4000));
    assert.equal(history[0].role, "user");
    assert.equal(history.some((turn) => turn.content === "Câu 0"), false);
    assert.equal(history.some((turn) => turn.content === "Câu 5"), true);
    assert.equal(history.at(-1).content.length, responseChars);
    page.requests[6].resolve(answer());
    await pending;
  }
});

test("failed requests and blocked turns do not enter later history", async () => {
  const page = createPage();
  let pending = page.submit("Câu được trả lời");
  page.requests[0].resolve(answer("Phản hồi trước"));
  await pending;
  pending = page.submit("Câu bị lỗi mạng");
  page.requests[1].reject();
  await pending;
  pending = page.submit("Yêu cầu bị chặn");
  assert.deepEqual(page.requests[2].payload.conversation_history, page.requests[1].payload.conversation_history);
  page.requests[2].resolve(answer("Yêu cầu bị chặn", "blocked"));
  await pending;
  pending = page.submit("Câu tiếp tục");
  assert.deepEqual(page.requests[3].payload.conversation_history, [
    { role: "user", content: "Câu được trả lời" }, { role: "assistant", content: "Phản hồi trước" }
  ]);
  page.requests[3].resolve(answer());
  await pending;
});

test("explicit new-question prefix clears both histories even after a failed request", async () => {
  const page = createPage();
  let pending = page.submit("Câu hỏi đang làm rõ");
  page.requests[0].resolve({ ...answer("Làm rõ", "needs_clarification"),
    continuation_context: { question: "Câu hỏi đang làm rõ", answers: [] } });
  await pending;
  pending = page.submit("Câu hỏi mới: Bạn là ai?");
  assert.deepEqual(page.requests[1].payload, { question: "Câu hỏi mới: Bạn là ai?" });
  page.requests[1].reject();
  await pending;
  pending = page.submit("Mình muốn hỏi lại");
  assert.deepEqual(page.requests[2].payload, { question: "Mình muốn hỏi lại" });
  page.requests[2].resolve(answer());
  await pending;
});

test("timeout aborts request, removes its loading marker and enables controls", async () => {
  const page = createPage();
  const pending = page.submit("Câu hỏi đất bị chậm");
  page.fireTimer(90000);
  assert.equal(page.requests[0].signal.aborted, true);
  assert.equal(await pending, false);
  assert.match(page.html(), /Yêu cầu quá 90 giây/);
  assert.equal(page.input.value, "Câu hỏi đất bị chậm");
  assert.deepEqual(page.loadingIds(), []);
  assert.equal(page.controlsDisabled(), false);
  assert.equal([...page.timers.values()].some((timer) => timer.delay === 90000), false);
});

test("HTTP failure with validation detail does not render object text or retain bogus context", async () => {
  const page = createPage();
  const pending = page.submit("Câu hỏi không hợp lệ");
  page.requests[0].resolve({ detail: [{ msg: "invalid" }],
    continuation_context: { question: "bogus", answers: [] } }, { ok: false });
  assert.equal(await pending, false);
  assert.match(page.html(), /Không thể xử lý câu hỏi/);
  assert.doesNotMatch(page.html(), /\[object Object\]/);
  assert.equal(page.controlsDisabled(), false);
});

test("invalid or excessive server continuation context is discarded", async () => {
  for (const context of [
    { question: "x".repeat(2001), answers: [] },
    { question: "Hỏi đất", answers: ["a", "b", "c", "d"] },
    { question: "Hỏi đất", answers: [null] },
    { question: "Hỏi đất", answers: ["x".repeat(2001)] }
  ]) {
    const page = createPage();
    let pending = page.submit("Hỏi đất");
    page.requests[0].resolve({ ...answer("Làm rõ", "needs_clarification"), continuation_context: context });
    await pending;
    pending = page.submit("Bổ sung");
    assert.equal("clarification_context" in page.requests[1].payload, false);
    page.requests[1].resolve(answer());
    await pending;
  }
});

test("health waits for actual runtime readiness and polls warming-up state", async () => {
  const page = createPage({ healthResponses: [
    { status: "warming_up", runtime: { ready: false }, artifacts_present: true },
    { status: "ready", runtime: { ready: true } }
  ] });
  await flush();
  assert.equal(page.nodes.get("#status-text").textContent, "Đang nạp kho tri thức");
  assert.equal(page.nodes.get("#status-dot").classes.has("ready"), false);
  page.fireTimer(2000);
  await flush();
  assert.equal(page.nodes.get("#status-text").textContent, "Kho tri thức sẵn sàng");
  assert.equal(page.healthCalls, 2);
});

test("health never calls file presence ready and warming-up polling is bounded", async () => {
  const notReady = createPage({ healthResponses: [{ status: "ready", artifacts_present: true }] });
  await flush();
  assert.equal(notReady.nodes.get("#status-dot").classes.has("ready"), false);
  const warming = createPage({ healthResponses: [{ status: "warming_up", runtime: { ready: false } }] });
  await flush();
  for (let index = 0; index < 29; index += 1) {
    warming.fireTimer(2000);
    await flush();
  }
  assert.equal(warming.healthCalls, 30);
  assert.equal(warming.timers.size, 0);
  assert.equal(warming.nodes.get("#status-text").textContent, "Kho tri thức chưa sẵn sàng. Hãy tải lại sau.");
});
