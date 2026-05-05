import anthropic
import streamlit as st
from dotenv import load_dotenv

from tools import TOOL_MAP, TOOLS

load_dotenv()

MODEL = "claude-opus-4-7"

st.set_page_config(
    page_title="Cassandra",
    page_icon="💬",
    layout="centered",
)

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

            if final.stop_reason != "tool_use":
                break

            tool_results = []
            for block in final.content:
                if block.type == "tool_use":
                    fn = TOOL_MAP.get(block.name)
                    result = fn(**block.input) if fn else f"Unknown tool: {block.name}"
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        }
                    )

            api_msgs.append({"role": "assistant", "content": final.content})
            api_msgs.append({"role": "user", "content": tool_results})

    st.session_state.messages.append({"role": "assistant", "content": full_text})
    st.session_state.api_messages = api_msgs
    st.session_state.api_messages.append({"role": "assistant", "content": full_text})
