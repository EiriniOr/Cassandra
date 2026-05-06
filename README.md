# Cassandra

A personal AI agent built on Claude (claude-opus-4-7). Runs as a CLI or a
streaming Streamlit web chat. Maintains a persistent memory wiki following
[Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## Setup

```bash
git clone https://github.com/EiriniOr/Cassandra.git
cd Cassandra
pip install -r requirements.txt
cp .env.example .env        # add ANTHROPIC_API_KEY
```

## Usage

**Web chat** (browser, streaming):

```bash
streamlit run app.py
```

**CLI**:

```bash
python main.py
```

On first use, Cassandra creates `~/cassandra-memory/` with the wiki layout
and a `CLAUDE.md` schema file the agent reads to know how to maintain it.

## Tools

Cassandra has 28 tools across 8 categories. The system prompt tells her
about all of them; she picks based on what helps.

### Web (Anthropic-hosted, no setup)

| Tool | What it does |
|---|---|
| `web_search` | Live web search via Anthropic. ~$10/1000 queries. |
| `web_fetch` | Fetch and read a URL. |

### Memory wiki (Karpathy LLM Wiki pattern)

Lives at `~/cassandra-memory/`:

```
raw/                    immutable source dump
wiki/
    index.md           master catalog
    log.md             chronological activity record
    entities/          people, organizations, products
    concepts/          ideas, frameworks, theories
    sources/           one-page summary per source in raw/
    synthesis/         cross-cutting analyses
CLAUDE.md              schema/instructions for the agent
```

| Tool | What it does |
|---|---|
| `memory_read` | Read a wiki page. |
| `memory_write` | Write a wiki page (markdown with frontmatter, `[[wiki-links]]`). |
| `memory_list` | List files in a subdir. |
| `memory_search` | Grep across all wiki markdown. |
| `memory_log` | Append timestamped entry to `wiki/log.md`. |

The flow: drop sources into `raw/` (or use `save_article` to fetch+save).
Ask Cassandra to ingest — she writes a `sources/` summary, updates `entities/`
and `concepts/`, logs the activity. Future questions hit `memory_search` first
so context compounds instead of being re-derived every time.

### Knowledge gathering

| Tool | What it does |
|---|---|
| `arxiv_search` | Search arXiv for recent papers. |
| `hn_top` | Top Hacker News stories. |
| `save_article` | Fetch a URL and save to memory `raw/` tagged with a project, ready for ingestion. |

### Files & shell

| Tool | What it does |
|---|---|
| `file_read` / `file_write` / `file_list` | General filesystem I/O. |
| `shell_exec` | Run shell commands. **Two-step**: dry-run first, user must say yes, then call with `confirm=true`. |
| `git_status` / `git_log` / `git_diff` | Inspect any local repo. |
| `project_picker` | Scan `~/` for git repos, sort by last commit. |

### Personal capture & recall

| Tool | What it does |
|---|---|
| `brain_dump` / `inbox_read` | Quick capture half-formed thoughts to a triaged inbox. |
| `log_decision` / `recall_decisions` | Decision journal with reasoning + expected outcome; recall by query. |

### Time

| Tool | What it does |
|---|---|
| `pomodoro_start` / `pomodoro_stop` / `pomodoro_summary` | 25-min focused work sessions; daily summary of where time went. |

### macOS

| Tool | What it does |
|---|---|
| `clipboard_read` / `clipboard_write` | Read/write the system clipboard. |
| `macos_notify` | Send a desktop notification. |

### Misc

| Tool | What it does |
|---|---|
| `calculate` | Safe math expression evaluator. |
| `tarot_draw` | Draw cards (single / three / celtic spread). For fun. |

## How it works

`tools/__init__.py` is the registry. Each tool module exports:

- A schema dict (sent to the API)
- A Python function (registered in `TOOL_MAP`, executed when the model calls it)

Anthropic-hosted tools (`web_search`, `web_fetch`) are declared in `TOOLS` but
have no `TOOL_MAP` entry — Anthropic runs them server-side and returns results
inline.

`main.py` and `app.py` share the same loop:

1. Send messages + `TOOLS` to the API.
2. If `stop_reason == "tool_use"`: dispatch each tool call via `TOOL_MAP`, send
   results back, repeat.
3. If `stop_reason == "pause_turn"`: server-side tool needs another iteration,
   continue without adding new user content.
4. Else: return the final text.

## Adding a new tool

1. Create `tools/my_tool.py`:

   ```python
   def my_tool(arg: str) -> str:
       return f"got {arg}"

   SCHEMA = {
       "name": "my_tool",
       "description": "What it does and when to use it.",
       "input_schema": {
           "type": "object",
           "properties": {"arg": {"type": "string"}},
           "required": ["arg"],
       },
   }
   ```

2. Register in `tools/__init__.py`:

   ```python
   from tools import my_tool
   CUSTOM_SCHEMAS.append(my_tool.SCHEMA)
   TOOL_MAP["my_tool"] = my_tool.my_tool
   ```

## Deploy online (claude.ai-like)

[Streamlit Community Cloud](https://share.streamlit.io) is the easy path:

1. Connect this repo
2. Set `ANTHROPIC_API_KEY` under **Settings → Secrets**
3. Deploy

⚠️ Most local tools won't work on Streamlit Cloud — `clipboard`, `macos_notify`,
`shell_exec`, `project_picker`, `git_*`, `file_*`, and the memory wiki all
assume your local filesystem. The hosted version is good for chat + web tools;
run locally for the full toolkit.

## Project Structure

```
Cassandra/
├── main.py              # CLI agent loop
├── app.py               # Streamlit web chat
├── tools/
│   ├── __init__.py      # Registry: TOOLS + TOOL_MAP
│   ├── calculator.py
│   ├── clipboard.py
│   ├── decisions.py
│   ├── files.py
│   ├── git_tools.py
│   ├── inbox.py
│   ├── knowledge.py     # arxiv, HN, save_article
│   ├── memory.py        # Karpathy LLM Wiki
│   ├── notify.py
│   ├── pomodoro.py
│   ├── projects.py
│   ├── shell.py
│   └── tarot.py
├── requirements.txt
├── .env.example
└── .gitignore
```

`main.py` and `app.py` are entry points; both import from `tools` and run the
same agent loop. The memory wiki at `~/cassandra-memory/` is the only state
that persists across sessions.
