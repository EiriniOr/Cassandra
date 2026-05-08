"""Reference page — every tool, what it does, and a sample prompt."""

import streamlit as st

from shared import MODEL

st.set_page_config(
    page_title="Cassandra · Tools",
    page_icon="🛠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    #MainMenu, footer, header { visibility: hidden; }
    .main .block-container { max-width: 1100px; padding-top: 1.5rem; }
    [data-testid="stSidebar"] { background: rgba(0,0,0,0.15); }
    .tool-card {
        border: 1px solid rgba(125,125,125,0.18);
        border-radius: 10px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.6rem;
        background: rgba(255,255,255,0.02);
        height: 100%;
    }
    .tool-name {
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-weight: 600;
        font-size: 0.95rem;
    }
    .tool-desc { opacity: 0.85; font-size: 0.92rem; margin: 0.4rem 0 0.6rem 0; }
    .tool-example {
        font-size: 0.85rem;
        opacity: 0.7;
        font-style: italic;
        border-left: 2px solid rgba(125,125,125,0.4);
        padding-left: 0.6rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


with st.sidebar:
    st.markdown("### 🔮 Cassandra")
    st.caption(f"`{MODEL}`")
    st.divider()
    st.caption("📁 Memory: `~/cassandra-memory/`")
    st.caption("🔗 [GitHub](https://github.com/EiriniOr/Cassandra)")


# (category_emoji+label, blurb, [(name, description, example_prompt), ...])
CATALOG = [
    (
        "🌐 Web",
        "Live information from outside Cassandra's training data.",
        [
            (
                "web_search",
                "Search the web. Anthropic-hosted, ~$10 per 1000 queries.",
                "What's been written recently about Karpathy's LLM Wiki?",
            ),
            (
                "web_fetch",
                "Fetch and read a single URL.",
                "Fetch https://news.ycombinator.com and tell me the top 3 themes.",
            ),
        ],
    ),
    (
        "🧠 Memory wiki",
        "The persistent second-brain at `~/cassandra-memory/`. Karpathy's LLM Wiki pattern: drop sources in `raw/`, ask for ingest, future questions hit memory first.",
        [
            (
                "memory_read",
                "Read a wiki page or any file under the memory directory.",
                "Read wiki/index.md",
            ),
            (
                "memory_write",
                "Write a wiki page (markdown with frontmatter and `[[wiki-links]]`). Cassandra uses this when ingesting sources.",
                "Ingest the article I just shared into the wiki.",
            ),
            (
                "memory_list",
                "List files in the memory dir.",
                "What's in my memory wiki?",
            ),
            (
                "memory_search",
                "Grep across all wiki markdown. Cassandra hits this first when answering from prior context.",
                "Search memory for 'agent loop'",
            ),
            (
                "memory_log",
                "Append a timestamped entry to wiki/log.md. Used during ingest.",
                "(Cassandra calls this herself when ingesting)",
            ),
        ],
    ),
    (
        "📥 Knowledge gathering",
        "Find sources and stage them for the wiki.",
        [
            (
                "arxiv_search",
                "Search arXiv for recent papers.",
                "Find recent arXiv papers on mixture-of-experts.",
            ),
            (
                "hn_top",
                "Top Hacker News stories.",
                "What's on Hacker News today?",
            ),
            (
                "save_article",
                "Fetch a URL, strip HTML, save to memory `raw/` tagged with a project. Stage for later ingestion.",
                "Save https://example.com/post to memory tagged 'cassandra' — note: useful for the agent loop pattern.",
            ),
        ],
    ),
    (
        "🗂 Files & shell",
        "Real access to your filesystem and tools. Shell is two-step: dry-run, your yes, then execute.",
        [
            (
                "file_read",
                "Read a text file from disk. Supports `~`.",
                "Read ~/notes/today.md",
            ),
            (
                "file_write",
                "Write or append to a file. Creates parent dirs.",
                "Write 'hello world' to ~/test.txt",
            ),
            (
                "file_list",
                "List a directory, optionally recursively.",
                "What's in ~/Documents?",
            ),
            (
                "shell_exec",
                "Run a shell command. Two-step: shows command first, requires explicit yes, then executes with confirm=true.",
                "Run du -sh ~/Desktop",
            ),
            (
                "git_status",
                "Run git status on a repo.",
                "What's the status of my Cassandra repo?",
            ),
            (
                "git_log",
                "Show recent commits.",
                "Show the last 5 commits in ~/data_suite",
            ),
            (
                "git_diff",
                "Show working-tree or staged diff.",
                "What did I change in app.py recently?",
            ),
            (
                "project_picker",
                "Scan ~/ for git repos, sort by last commit time.",
                "What should I work on next?",
            ),
        ],
    ),
    (
        "💭 Personal capture & recall",
        "Lightweight journal. Plain markdown you can grep yourself.",
        [
            (
                "brain_dump",
                "Capture a half-formed thought to the inbox with timestamp.",
                "Brain dump: idea — agent that drafts cold emails from LinkedIn",
            ),
            (
                "inbox_read",
                "Read the entire inbox.",
                "What's in my inbox?",
            ),
            (
                "log_decision",
                "Append a decision with reasoning and expected outcome.",
                "Log this decision: chose Streamlit because of speed-to-ship; expected to deploy in a day.",
            ),
            (
                "recall_decisions",
                "Search past decisions, optionally by query.",
                "What did I decide about hosting?",
            ),
        ],
    ),
    (
        "⏱ Time",
        "Pomodoro-style work tracking. 25-min sessions logged to JSON for end-of-day review.",
        [
            (
                "pomodoro_start",
                "Start a focused work session (default 25 min).",
                "Start a 25-min pomodoro for refactoring auth.",
            ),
            (
                "pomodoro_stop",
                "End the current session, optionally with notes.",
                "Stop the timer — finished the migration.",
            ),
            (
                "pomodoro_summary",
                "Show all sessions for a date (default today).",
                "How did today go?",
            ),
        ],
    ),
    (
        "💻 macOS",
        "Local-only. Won't work on Streamlit Cloud.",
        [
            (
                "clipboard_read",
                "Read the macOS clipboard.",
                "What did I just copy?",
            ),
            (
                "clipboard_write",
                "Write text to the clipboard.",
                "Copy 'me@example.com' to my clipboard.",
            ),
            (
                "macos_notify",
                "Send a desktop notification.",
                "Notify me when this is done.",
            ),
        ],
    ),
    (
        "✨ Misc",
        "",
        [
            (
                "calculate",
                "Safe math expression evaluator. Supports trig, log, sqrt, pi/e/tau.",
                "What's sqrt(2) * pi?",
            ),
            (
                "tarot_draw",
                "Draw tarot cards (single / three / celtic spread). For fun.",
                "Draw three tarot cards about my next decision.",
            ),
        ],
    ),
]


st.title("🛠 Tools")
st.caption(
    "Cassandra picks tools based on what you ask. You don't call them directly — "
    "you just chat. The examples below are sample prompts that tend to trigger each tool."
)

total = sum(len(tools) for _, _, tools in CATALOG)
st.caption(f"**{total} tools** across {len(CATALOG)} categories.")
st.divider()


for header, blurb, tools in CATALOG:
    st.markdown(f"### {header}")
    if blurb:
        st.caption(blurb)
    cols = st.columns(2)
    for i, (name, desc, example) in enumerate(tools):
        with cols[i % 2]:
            st.markdown(
                f"""
<div class="tool-card">
    <div class="tool-name">{name}</div>
    <div class="tool-desc">{desc}</div>
    <div class="tool-example">Try: "{example}"</div>
</div>
""",
                unsafe_allow_html=True,
            )
    st.write("")
