# Cassandra

A personal AI agent on Claude Opus 4.7 with **30 tools** and a persistent memory wiki ([Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)). Runs locally — FastAPI backend + a custom web UI.

## Setup

```bash
git clone https://github.com/EiriniOr/Cassandra.git
cd Cassandra
pip install -r requirements.txt
cp .env.example .env       # then put your ANTHROPIC_API_KEY in .env
```

## Run

**One-click:** double-click `launch.command` in Finder, or the `Cassandra.command` shortcut on your desktop. Auto-installs deps if needed, starts the server, opens the browser.

**From the terminal:**

```bash
python server.py
```

Then open <http://localhost:8000>. Server binds to `127.0.0.1` only — not accessible from other machines on your network.

**CLI** (no browser, terminal only):

```bash
python main.py
```

The memory wiki at `~/cassandra-memory/` auto-creates on first use.

## Tools

Cassandra picks tools based on what you ask — you don't call them directly. The `/tools` page in the app documents all 30 with sample prompts. Quick overview:

| Group | Tools |
|---|---|
| **Web** | `web_search`, `web_fetch` (Anthropic-hosted) |
| **Memory wiki** | `memory_read`, `memory_write`, `memory_list`, `memory_search`, `memory_log` — second brain at `~/cassandra-memory/` |
| **Knowledge** | `arxiv_search`, `hn_top`, `save_article` (drops sources into wiki `raw/`) |
| **Files & shell** | `file_read`, `file_write`, `file_list`, `shell_exec` (two-step confirm), `git_status`, `git_log`, `git_diff`, `project_picker` |
| **Capture** | `brain_dump`, `inbox_read`, `log_decision`, `recall_decisions` |
| **Time** | `pomodoro_start`, `pomodoro_stop`, `pomodoro_summary` |
| **macOS** | `clipboard_read`, `clipboard_write`, `macos_notify` |
| **Misc** | `calculate`, `tarot_draw` |

## Architecture

```
Browser  ──(SSE stream)──>  FastAPI (server.py)
                                │
                                ├── Anthropic SDK  →  Claude Opus 4.7
                                └── tools/  →  TOOL_MAP[name](**input)
```

- `server.py` — FastAPI app, `/api/chat` endpoint streams Server-Sent Events
- `static/` — handwritten HTML/CSS/JS (no framework)
- `tools/` — one module per tool, registered in `tools/__init__.py`
- `shared.py` — system prompt + model id (imported by `server.py` and `main.py`)

## Adding a tool

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

3. Update the Tools reference page (`static/tools.html`) so the UI shows it.

## Project structure

```
Cassandra/
├── server.py            # FastAPI backend (SSE chat endpoint)
├── main.py              # CLI agent loop
├── shared.py            # SYSTEM prompt + MODEL constants
├── launch.command       # double-click launcher (macOS)
├── static/
│   ├── index.html       # chat UI
│   ├── tools.html       # tools reference
│   ├── style.css        # all styles (dark + violet/gold)
│   └── chat.js          # streaming chat client
├── tools/               # 28 custom tools + registry
│   ├── __init__.py
│   ├── calculator.py
│   ├── clipboard.py
│   ├── decisions.py
│   ├── files.py
│   ├── git_tools.py
│   ├── inbox.py
│   ├── knowledge.py
│   ├── memory.py
│   ├── notify.py
│   ├── pomodoro.py
│   ├── projects.py
│   ├── shell.py
│   └── tarot.py
├── requirements.txt
├── .env.example
└── .gitignore
```
