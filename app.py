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

st.set_page_config(page_title="Cassandra", page_icon="💬", layout="centered")
st.title("Cassandra")
st.caption(f"AI Agent · {MODEL}")


@st.cache_resource
def get_client():
    return anthropic.Anthropic()


client = get_client()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_messages" not in st.session_state:
    st.session_state.api_messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Send a message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.api_messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    api_msgs = list(st.session_state.api_messages)

    with st.chat_message("assistant"):
        full_text = ""
        placeholder = st.empty()

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
                    placeholder.markdown(full_text + chunk_text + "▌")
                final = stream.get_final_message()

            full_text += chunk_text
            placeholder.markdown(full_text)

            if final.stop_reason == "pause_turn":
                api_msgs.append({"role": "assistant", "content": final.content})
                continue

            if final.stop_reason != "tool_use":
                break

            tool_results = []
            with st.status("Running tools...", expanded=False) as status:
                for block in final.content:
                    if block.type == "tool_use":
                        st.write(f"→ `{block.name}`")
                        fn = TOOL_MAP.get(block.name)
                        if not fn:
                            result = f"Unknown tool: {block.name}"
                        else:
                            try:
                                result = fn(**block.input)
                            except Exception as exc:
                                result = f"Error executing {block.name}: {exc}"
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": str(result),
                            }
                        )
                status.update(
                    label=f"Ran {len(tool_results)} tool(s)", state="complete"
                )

            api_msgs.append({"role": "assistant", "content": final.content})
            api_msgs.append({"role": "user", "content": tool_results})

    st.session_state.messages.append({"role": "assistant", "content": full_text})
    st.session_state.api_messages = api_msgs
    st.session_state.api_messages.append({"role": "assistant", "content": full_text})
