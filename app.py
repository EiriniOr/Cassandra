import json

import anthropic
import streamlit as st
from dotenv import load_dotenv

from tools import TOOL_MAP, TOOLS

load_dotenv()

MODEL = "claude-opus-4-7"

SYSTEM = """You are Cassandra, a personal AI agent for Eirini. You have access to:

- Web search and fetch (Anthropic-hosted)
- A persistent memory wiki at ~/cassandra-memory/ following Karpathy's LLM Wiki
  pattern. Read ~/cassandra-memory/CLAUDE.md to learn the schema. When the user
  asks about prior context, search memory FIRST. When they share something
  worth remembering, ingest it: write a source page, update entities/concepts,
  append to log.md.
- File read/write (general filesystem)
- Calculator, clipboard, macOS notifications
- Project picker (scans ~/ for git repos)
- Decision journal, brain dump inbox
- Shell execution (TWO-STEP — always show command first, get user yes, then
  call again with confirm=true)
- Git inspector (status, log, diff)
- Pomodoro time tracker
- Knowledge fetchers: arXiv, Hacker News, save_article (drops sources into
  the memory raw/ dir for later wiki ingestion)
- Tarot draw (for fun)

Be concise. Use tools when they actually help."""


st.set_page_config(
    page_title="Cassandra",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
<style>
    #MainMenu, footer, header { visibility: hidden; }
    .main .block-container {
        max-width: 780px;
        padding-top: 1.5rem;
        padding-bottom: 8rem;
    }
    [data-testid="stChatMessage"] {
        background: transparent;
        padding: 0.6rem 0;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
        line-height: 1.65;
    }
    [data-testid="stSidebar"] {
        background: rgba(0,0,0,0.15);
    }
    .welcome-title {
        font-size: 2.4rem;
        font-weight: 600;
        text-align: center;
        margin-bottom: 0.4rem;
    }
    .welcome-sub {
        text-align: center;
        opacity: 0.6;
        margin-bottom: 2.5rem;
    }
    .stButton > button {
        text-align: left;
        white-space: normal;
        height: auto;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        line-height: 1.4;
    }
    div[data-testid="stExpander"] {
        border: 1px solid rgba(125, 125, 125, 0.18);
        border-radius: 10px;
        margin: 0.4rem 0;
    }
    div[data-testid="stExpander"] summary {
        font-size: 0.85rem;
        opacity: 0.75;
    }
    .stChatInputContainer {
        border-radius: 16px;
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


with st.sidebar:
    st.markdown("### 🔮 Cassandra")
    st.caption(f"`{MODEL}`")

    if st.button("✨  New chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.api_messages = []
        st.rerun()

    st.divider()

    custom_count = sum(1 for t in TOOLS if "input_schema" in t)
    server_count = len(TOOLS) - custom_count
    st.markdown(f"**🧰 Tools** · {len(TOOLS)} total")
    st.caption(f"{server_count} server-hosted · {custom_count} local")

    with st.expander("Tool list", expanded=False):
        for t in TOOLS:
            st.markdown(f"`{t.get('name')}`")

    st.divider()
    st.caption("📁 Memory: `~/cassandra-memory/`")
    st.caption("🔗 [GitHub](https://github.com/EiriniOr/Cassandra)")


SUGGESTIONS = [
    (
        "📚  Catch me up",
        "What's been on Hacker News today, and any new arXiv papers on agentic LLMs?",
    ),
    (
        "🗂️  What to work on?",
        "Use project_picker to scan my repos. Suggest what to focus on next.",
    ),
    (
        "🧠  Survey my memory",
        "List what's in my memory wiki and summarize what I have so far.",
    ),
    ("🔮  Read my week", "Draw three tarot cards for the week ahead."),
]


def render_message(msg: dict):
    avatar = "🔮" if msg["role"] == "assistant" else None
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
    st.markdown("<div class='welcome-title'>🔮 Cassandra</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='welcome-sub'>Personal AI agent · 30 tools · persistent memory</div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, (label, prompt_text) in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(label, key=f"sug_{i}", use_container_width=True):
                st.session_state["pending_prompt"] = prompt_text
                st.rerun()


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

    with st.chat_message("assistant", avatar="🔮"):
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
