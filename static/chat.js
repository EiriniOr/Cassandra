// ─── State ───────────────────────────────────────────────────────────────────
const history = []; // {role, content} — sent to backend each turn

const $messages = document.getElementById("messages");
const $welcome = document.getElementById("welcome");
const $input = document.getElementById("input");
const $send = document.getElementById("send");
const $composer = document.getElementById("composer");
const $newChat = document.getElementById("new-chat");
const $toolCount = document.getElementById("tool-count");

// ─── Helpers ─────────────────────────────────────────────────────────────────
function el(tag, attrs = {}, ...kids) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
        if (k === "class") e.className = v;
        else if (k === "html") e.innerHTML = v;
        else e.setAttribute(k, v);
    }
    for (const k of kids) e.append(k?.nodeType ? k : document.createTextNode(k));
    return e;
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        $messages.scrollTop = $messages.scrollHeight;
    });
}

function autoresize() {
    $input.style.height = "auto";
    $input.style.height = Math.min($input.scrollHeight, 200) + "px";
}

// Minimal Markdown — supports paragraphs, **bold**, *italic*, `code`,
// ```code blocks```, ## headings, > quotes, [links](url), - lists, 1. lists.
function escapeHtml(s) {
    return s
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function renderMarkdown(text) {
    if (!text) return "";

    // Extract code fences first to protect their contents
    const fences = [];
    text = text.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
        const i = fences.length;
        fences.push(`<pre><code>${escapeHtml(code)}</code></pre>`);
        return `\x00FENCE${i}\x00`;
    });

    // Escape everything else first
    text = escapeHtml(text);

    // Inline code
    text = text.replace(/`([^`\n]+)`/g, "<code>$1</code>");

    // Bold + italic
    text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    text = text.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, "<em>$1</em>");

    // Links
    text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');

    // Headings + blockquotes + lists (line-based)
    const lines = text.split("\n");
    const out = [];
    let inList = null; // "ul" | "ol" | null
    let paraBuf = [];

    const flushPara = () => {
        if (paraBuf.length) {
            out.push(`<p>${paraBuf.join("<br>")}</p>`);
            paraBuf = [];
        }
    };
    const closeList = () => {
        if (inList) {
            out.push(`</${inList}>`);
            inList = null;
        }
    };

    for (const raw of lines) {
        const line = raw;
        // Heading
        const h = line.match(/^(#{1,3})\s+(.+)$/);
        if (h) {
            flushPara(); closeList();
            const level = h[1].length;
            out.push(`<h${level}>${h[2]}</h${level}>`);
            continue;
        }
        // Blockquote
        if (/^&gt;\s/.test(line)) {
            flushPara(); closeList();
            out.push(`<blockquote>${line.replace(/^&gt;\s/, "")}</blockquote>`);
            continue;
        }
        // Unordered list
        if (/^[-*]\s+/.test(line)) {
            flushPara();
            if (inList !== "ul") { closeList(); out.push("<ul>"); inList = "ul"; }
            out.push(`<li>${line.replace(/^[-*]\s+/, "")}</li>`);
            continue;
        }
        // Ordered list
        if (/^\d+\.\s+/.test(line)) {
            flushPara();
            if (inList !== "ol") { closeList(); out.push("<ol>"); inList = "ol"; }
            out.push(`<li>${line.replace(/^\d+\.\s+/, "")}</li>`);
            continue;
        }
        // Blank → paragraph break
        if (line.trim() === "") {
            flushPara(); closeList();
            continue;
        }
        // Default → paragraph line
        if (inList) closeList();
        paraBuf.push(line);
    }
    flushPara(); closeList();

    let html = out.join("\n");
    // Restore code fences
    html = html.replace(/\x00FENCE(\d+)\x00/g, (_, i) => fences[Number(i)]);
    return html;
}

// ─── Message rendering ──────────────────────────────────────────────────────
function addUserMessage(text) {
    const wrap = el("div", { class: "msg msg-user" },
        el("div", { class: "msg-body", html: renderMarkdown(text) }),
    );
    $messages.append(wrap);
    scrollToBottom();
}

function addAssistantBubble() {
    const body = el("div", { class: "msg-body" });
    const textEl = el("div", { class: "msg-text" });
    const cursor = el("span", { class: "cursor" });
    body.append(textEl);
    body.append(cursor);
    const wrap = el("div", { class: "msg msg-assistant" },
        el("div", { class: "msg-avatar" }, "🔮"),
        body,
    );
    $messages.append(wrap);
    scrollToBottom();
    return { wrap, body, textEl, cursor, rawText: "" };
}

function addToolCard(bubble, { id, name, input }) {
    const head = el("div", { class: "tool-head" },
        el("span", { class: "tool-name" }, name),
        el("span", { class: "tool-status" },
            el("span", { class: "spinner" }),
            el("span", {}, "running"),
        ),
    );
    head.append(el("span", { class: "chevron" }, "▾"));
    const inputBlock = el("div", { class: "tool-content" }, JSON.stringify(input, null, 2));
    const resultBlock = el("div", { class: "tool-content" }, "…");
    const body = el("div", { class: "tool-body" },
        el("div", { class: "tool-section-label" }, "Input"),
        inputBlock,
        el("div", { class: "tool-section-label" }, "Result"),
        resultBlock,
    );
    const card = el("div", { class: "tool-call", "data-id": id }, head, body);
    head.addEventListener("click", () => {
        card.dataset.open = card.dataset.open === "true" ? "false" : "true";
    });
    bubble.body.insertBefore(card, bubble.textEl);
    scrollToBottom();
    return { card, head, resultBlock };
}

function finishToolCard(toolUI, resultText) {
    toolUI.resultBlock.textContent = resultText;
    const status = toolUI.head.querySelector(".tool-status");
    if (status) {
        status.innerHTML = "";
        status.append(document.createTextNode("done"));
    }
}

function addErrorBanner(msg) {
    const e = el("div", { class: "error-banner" }, msg);
    $messages.append(e);
    scrollToBottom();
}

// ─── SSE / chat loop ────────────────────────────────────────────────────────
function setBusy(on) {
    $send.disabled = on;
    $input.disabled = on;
}

async function sendMessage(text) {
    if ($welcome) $welcome.classList.add("hidden");

    addUserMessage(text);
    history.push({ role: "user", content: text });
    setBusy(true);

    const bubble = addAssistantBubble();
    const toolMap = new Map(); // id → toolUI

    try {
        const resp = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ messages: history }),
        });
        if (!resp.ok || !resp.body) {
            throw new Error(`HTTP ${resp.status}`);
        }

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            buf += decoder.decode(value, { stream: true });

            const events = buf.split("\n\n");
            buf = events.pop() ?? "";

            for (const block of events) {
                if (!block.trim()) continue;
                let event = "message", data = "";
                for (const line of block.split("\n")) {
                    if (line.startsWith("event: ")) event = line.slice(7).trim();
                    else if (line.startsWith("data: ")) data += line.slice(6);
                }
                let payload;
                try { payload = JSON.parse(data); } catch { continue; }

                if (event === "text") {
                    bubble.rawText += payload.text;
                    bubble.textEl.innerHTML = renderMarkdown(bubble.rawText);
                    scrollToBottom();
                } else if (event === "tool_use") {
                    const ui = addToolCard(bubble, payload);
                    toolMap.set(payload.id, ui);
                } else if (event === "tool_result") {
                    const ui = toolMap.get(payload.id);
                    if (ui) finishToolCard(ui, payload.result);
                } else if (event === "text_break") {
                    // New text after tool call — keep rawText, model continues
                } else if (event === "error") {
                    addErrorBanner(payload.message ?? "Unknown error");
                } else if (event === "done") {
                    // nothing — outer loop ends when stream closes
                }
            }
        }
    } catch (err) {
        addErrorBanner(`Request failed: ${err.message}`);
    } finally {
        bubble.cursor.remove();
        // store assistant text in history so multi-turn works
        if (bubble.rawText) {
            history.push({ role: "assistant", content: bubble.rawText });
        }
        setBusy(false);
        $input.focus();
    }
}

// ─── Input handling ─────────────────────────────────────────────────────────
$input.addEventListener("input", autoresize);
$input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        $composer.dispatchEvent(new Event("submit", { cancelable: true }));
    }
});

$composer.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = $input.value.trim();
    if (!text || $send.disabled) return;
    $input.value = "";
    autoresize();
    sendMessage(text);
});

$newChat.addEventListener("click", () => {
    history.length = 0;
    $messages.innerHTML = "";
    if ($welcome) {
        $welcome.classList.remove("hidden");
        $messages.append($welcome);
    }
    $input.focus();
});

document.querySelectorAll(".suggestion").forEach((btn) => {
    btn.addEventListener("click", () => {
        const prompt = btn.dataset.prompt;
        if (prompt) sendMessage(prompt);
    });
});

// Tool count for sidebar
fetch("/api/tools").then((r) => r.json()).then((data) => {
    $toolCount.textContent = `${data.tools.length}`;
}).catch(() => { $toolCount.textContent = "?"; });

// Move welcome into messages stream so it scrolls
if ($welcome && $welcome.parentNode !== $messages) {
    $messages.append($welcome);
}
