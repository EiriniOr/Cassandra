import json

import anthropic
import streamlit as st

from shared import MODEL, SYSTEM, render_signout_button, require_auth
from tools import TOOL_MAP, TOOLS

st.set_page_config(
    page_title="Cassandra",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

require_auth()


# ── Theme & CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;0,9..144,600;1,9..144,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
    :root {
        --violet: #a78bfa;
        --violet-soft: rgba(167, 139, 250, 0.08);
        --violet-line: rgba(167, 139, 250, 0.18);
        --gold: #d4b15c;
        --bg: #0a0915;
        --card: rgba(167, 139, 250, 0.04);
        --text: #ece9f5;
        --muted: #9b97b8;
    }

    /* Hide Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stStatusWidget"] { display: none; }

    /* Body & layout */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, system-ui, sans-serif;
    }
    .main .block-container {
        max-width: 780px;
        padding-top: 1.5rem;
        padding-bottom: 9rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(167,139,250,0.06) 0%, rgba(0,0,0,0.2) 100%);
        border-right: 1px solid var(--violet-line);
    }
    [data-testid="stSidebar"] h3 {
        font-family: 'Fraunces', Georgia, serif;
        font-weight: 500;
        letter-spacing: 0.01em;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(167, 139, 250, 0.06);
        border: 1px solid var(--violet-line);
        color: var(--text);
        font-weight: 500;
        transition: all 0.15s ease;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(167, 139, 250, 0.14);
        border-color: var(--violet);
        transform: translateY(-1px);
    }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        background: transparent;
        padding: 0.5rem 0.2rem;
        border-radius: 12px;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]),
    [data-testid="stChatMessage"]:has(img[alt="assistant avatar"]) {
        background: var(--card);
        border: 1px solid var(--violet-line);
        padding: 0.9rem 1.1rem;
        margin: 0.6rem 0;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
        line-height: 1.7;
        font-size: 0.97rem;
    }
    [data-testid="stChatMessage"] code {
        background: rgba(167, 139, 250, 0.12);
        color: #d8c8ff;
        font-family: 'JetBrains Mono', SFMono-Regular, monospace;
        font-size: 0.88em;
        padding: 0.1rem 0.35rem;
        border-radius: 4px;
    }

    /* Chat input */
    [data-testid="stChatInput"] {
        background: rgba(20, 18, 32, 0.95);
        border: 1px solid var(--violet-line);
        border-radius: 14px;
        backdrop-filter: blur(8px);
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: var(--violet);
        box-shadow: 0 0 0 1px var(--violet);
    }

    /* Welcome screen */
    .welcome-wrap {
        text-align: center;
        margin-top: 3rem;
        margin-bottom: 2.8rem;
    }
    .welcome-mark {
        font-size: 2.6rem;
        color: var(--violet);
        letter-spacing: 0.4em;
        margin-bottom: 0.4rem;
        opacity: 0.85;
    }
    .welcome-title {
        font-family: 'Fraunces', Georgia, serif;
        font-weight: 400;
        font-size: 3.2rem;
        line-height: 1.05;
        letter-spacing: -0.01em;
        background: linear-gradient(135deg, #ece9f5 30%, var(--violet) 70%, var(--gold) 100%);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 0.8rem 0;
    }
    .welcome-tagline {
        font-family: 'Fraunces', Georgia, serif;
        font-style: italic;
        color: var(--muted);
        font-size: 1.05rem;
        margin-bottom: 0.4rem;
    }
    .welcome-meta {
        color: var(--muted);
        font-size: 0.85rem;
        opacity: 0.75;
    }

    /* Suggestion buttons (main area) */
    .main .stButton > button {
        text-align: left;
        white-space: normal;
        height: auto;
        padding: 1rem 1.1rem;
        border-radius: 12px;
        line-height: 1.45;
        background: var(--card);
        border: 1px solid var(--violet-line);
        color: var(--text);
        font-weight: 500;
        transition: all 0.18s ease;
    }
    .main .stButton > button:hover {
        background: rgba(167, 139, 250, 0.12);
        border-color: var(--violet);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(167, 139, 250, 0.1);
    }

    /* Tool-call expanders */
    div[data-testid="stExpander"] {
        border: 1px solid var(--violet-line);
        border-radius: 10px;
        margin: 0.5rem 0;
        background: rgba(167, 139, 250, 0.025);
        transition: border-color 0.15s ease;
    }
    div[data-testid="stExpander"]:hover {
        border-color: rgba(167, 139, 250, 0.35);
    }
    div[data-testid="stExpander"] summary {
        font-size: 0.86rem;
        opacity: 0.85;
        padding: 0.5rem 0.8rem;
        font-weight: 500;
    }
    div[data-testid="stExpander"] summary p code {
        background: rgba(212, 177, 92, 0.12);
        color: var(--gold);
    }

    /* Code blocks */
    .stCodeBlock {
        background: #110f1c !important;
        border: 1px solid var(--violet-line);
        border-radius: 8px;
    }

    /* Captions */
    [data-testid="stCaptionContainer"] {
        color: var(--muted);
    }

    /* Login form polish */
    [data-testid="stForm"] {
        background: var(--card);
        border: 1px solid var(--violet-line);
        border-radius: 16px;
        padding: 1.5rem;
    }

    /* Selection color */
    ::selection {
        background: rgba(167, 139, 250, 0.35);
        color: var(--text);
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def get_client():
    return anthropic.Anthropic()


client = get_client()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_messages" not in st.session_state:
    st.session_state.api_messages = []


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ✦ Cassandra")
    st.caption(f"`{MODEL}`")

    st.write("")

    if st.button("✨  New chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.api_messages = []
        st.rerun()

    st.divider()

    custom_count = sum(1 for t in TOOLS if "input_schema" in t)
    server_count = len(TOOLS) - custom_count
    st.markdown(f"**🛠  Tools** · {len(TOOLS)} total")
    st.caption(f"{server_count} server-hosted · {custom_count} local")

    with st.expander("Show all tools", expanded=False):
        for t in TOOLS:
            st.markdown(f"`{t.get('name')}`")

    st.divider()
    st.caption("📁 Memory: `~/cassandra-memory/`")
    st.caption("🔗 [GitHub](https://github.com/EiriniOr/Cassandra)")

    st.divider()
    render_signout_button()


# ── Welcome / Suggestions ──────────────────────────────────────────────────────
SUGGESTIONS = [
    (
        "📚",
        "Catch me up",
        "Latest from arXiv and HN",
        "What's been on Hacker News today, and any new arXiv papers on agentic LLMs?",
    ),
    (
        "🗂️",
        "What should I work on?",
        "Scan my repos and suggest",
        "Use project_picker to scan my repos. Suggest what to focus on next.",
    ),
    (
        "🧠",
        "Survey my memory",
        "What's in the wiki so far",
        "List what's in my memory wiki and summarize what I have so far.",
    ),
    (
        "🔮",
        "Read my week",
        "Three-card tarot spread",
        "Draw three tarot cards for the week ahead.",
    ),
]


def render_message(msg: dict):
    avatar = "✦" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        for tool in msg.get("tool_calls", []):
            with st.expander(f"🛠  `{tool['name']}`", expanded=False):
                if tool.get("input"):
                    st.code(tool["input"], language="json")
                if tool.get("result"):
                    st.markdown("**Result**")
                    st.code(tool["result"][:2000], language=None)
        if msg.get("content"):
            st.markdown(msg["content"])


for msg in st.session_state.messages:
    render_message(msg)


if not st.session_state.messages:
    st.markdown(
        """
<div class='welcome-wrap'>
    <div class='welcome-mark'>✦</div>
    <h1 class='welcome-title'>Cassandra</h1>
    <div class='welcome-tagline'>An oracle with thirty hands.</div>
    <div class='welcome-meta'>Personal AI agent · persistent memory · 30 tools</div>
</div>
""",
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, (icon, label, sub, prompt_text) in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(
                f"{icon}  **{label}**\n\n{sub}",
                key=f"sug_{i}",
                use_container_width=True,
            ):
                st.session_state["pending_prompt"] = prompt_text
                st.rerun()


# ── Chat ───────────────────────────────────────────────────────────────────────
prompt = st.chat_input("Message Cassandra...") or st.session_state.pop(
    "pending_prompt", None
)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.api_messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    api_msgs = list(st.session_state.api_messages)
    tool_calls_for_msg = []

    with st.chat_message("assistant", avatar="✦"):
        full_text = ""
        text_placeholder = st.empty()

        while True:
            chunk_text = ""
            with client.messages.stream(
                model=MODEL,
                max_tokens=8192,
                system=SYSTEM,
                messages=api_msgs,
                tools=TOOLS,
                thinking={"type": "adaptive"},
            ) as stream:
                for chunk in stream.text_stream:
                    chunk_text += chunk
                    text_placeholder.markdown(full_text + chunk_text + "▌")
                final = stream.get_final_message()

            full_text += chunk_text
            text_placeholder.markdown(full_text)

            if final.stop_reason == "pause_turn":
                api_msgs.append({"role": "assistant", "content": final.content})
                continue

            if final.stop_reason != "tool_use":
                break

            tool_results = []
            for block in final.content:
                if block.type != "tool_use":
                    continue

                input_str = json.dumps(block.input, indent=2) if block.input else ""

                with st.expander(f"🛠  `{block.name}`", expanded=False):
                    if input_str:
                        st.code(input_str, language="json")
                    spinner = st.empty()
                    spinner.caption("running...")

                    fn = TOOL_MAP.get(block.name)
                    if not fn:
                        result = f"Unknown tool: {block.name}"
                    else:
                        try:
                            result = fn(**block.input)
                        except Exception as exc:
                            result = f"Error: {exc}"

                    spinner.empty()
                    st.markdown("**Result**")
                    st.code(str(result)[:2000], language=None)

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    }
                )
                tool_calls_for_msg.append(
                    {
                        "name": block.name,
                        "input": input_str,
                        "result": str(result),
                    }
                )

            api_msgs.append({"role": "assistant", "content": final.content})
            api_msgs.append({"role": "user", "content": tool_results})

            text_placeholder = st.empty()
            full_text = ""

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_text,
            "tool_calls": tool_calls_for_msg,
        }
    )
    st.session_state.api_messages = api_msgs
    st.session_state.api_messages.append({"role": "assistant", "content": full_text})
