"""Shared across app.py and pages/. Auth, system prompt, model id."""

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_secret(key: str) -> str | None:
    """Streamlit Cloud secrets first, then local env / .env."""
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key)


# Make the Anthropic key visible to anthropic.Anthropic() (which reads from env).
_api_key = get_secret("ANTHROPIC_API_KEY")
if _api_key:
    os.environ["ANTHROPIC_API_KEY"] = _api_key


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


def require_auth():
    """Block the page until user signs in. Credentials from env."""
    if st.session_state.get("authed"):
        return

    expected_user = get_secret("CASSANDRA_USER")
    expected_pass = get_secret("CASSANDRA_PASS")

    if not expected_user or not expected_pass:
        st.error(
            "Auth not configured. Set `CASSANDRA_USER` and `CASSANDRA_PASS` in "
            "`.env` (local) or Streamlit Cloud Secrets (deployed)."
        )
        st.stop()

    st.markdown(
        "<div style='text-align:center;font-size:3rem;margin-top:4rem;'>🔮</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='text-align:center;opacity:0.6;margin-bottom:2rem;'>Cassandra</div>",
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        with st.form("login", clear_on_submit=False):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)
            if submitted:
                if u == expected_user and p == expected_pass:
                    st.session_state.authed = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    st.stop()


def render_signout_button():
    """Call inside a sidebar context."""
    if st.button("🚪  Sign out", use_container_width=True):
        for key in ("authed", "messages", "api_messages"):
            st.session_state.pop(key, None)
        st.rerun()
