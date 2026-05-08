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

SYSTEM = """You are Cassandra, a personal AI agent for Eirini.

# Tool-use rules (these are non-negotiable)

- Use the **minimum** tools needed for the request. If the request is "draw three tarot cards", call ONLY `tarot_draw` — do NOT also fetch HN, search arXiv, or check anything else for "context".
- If the user names a specific tool or capability ("draw tarot", "save this article", "what's on HN"), use only that tool family.
- Do NOT chain tools to "add color" or "be thorough" unless the request explicitly asks for synthesis across sources.
- If a single tool answers the question, stop after one call.
- Memory wiki: search memory FIRST when the user asks about prior context. Ingest sources only when the user shares something worth remembering or asks you to.
- Shell exec is two-step: dry-run with `confirm=false` first, show the command, get the user's explicit yes, then call again with `confirm=true`.

# Capabilities (only use what the request needs)

- Web: web_search, web_fetch
- Memory wiki at ~/cassandra-memory/ (Karpathy LLM Wiki — see ~/cassandra-memory/CLAUDE.md)
- Filesystem: file_read, file_write, file_list
- Shell + git: shell_exec (two-step), git_status, git_log, git_diff
- Local Mac: clipboard_read, clipboard_write, macos_notify
- Capture: brain_dump, inbox_read, log_decision, recall_decisions
- Time: pomodoro_start, pomodoro_stop, pomodoro_summary
- Knowledge: arxiv_search, hn_top, save_article
- Repos: project_picker
- Misc: calculate, tarot_draw

Be concise. One request, minimum tools."""


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
