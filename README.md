# Cassandra

An AI agent built on [Claude](https://anthropic.com) (claude-opus-4-7). Runs as a CLI or a streaming web chat you can deploy online.

## Setup

```bash
git clone https://github.com/EiriniOr/Cassandra.git
cd Cassandra
pip install -r requirements.txt
cp .env.example .env        # add your ANTHROPIC_API_KEY
```

## Usage

**Web chat** (runs locally at `http://localhost:8501`):
```bash
streamlit run app.py
```

**CLI**:
```bash
python main.py
```

## Adding Tools

1. Define the tool function in `tools/` (e.g. `tools/search.py`)
2. Register it in `tools/__init__.py`:

```python
from tools.search import web_search

TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for current information.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    }
]

TOOL_MAP = {
    "web_search": web_search,
}
```

## Deploy Online (like claude.ai)

Deploy the web chat to [Streamlit Community Cloud](https://streamlit.io/cloud) for free:

1. Push this repo to GitHub (already done)
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo
3. Set `ANTHROPIC_API_KEY` under **Settings → Secrets**
4. Deploy — you get a public URL you can share

## Project Structure

```
Cassandra/
├── main.py          # CLI agent loop
├── app.py           # Streamlit web chat
├── tools/
│   └── __init__.py  # Tool registry (TOOLS list + TOOL_MAP dict)
├── requirements.txt
├── .env.example
└── .gitignore
```

`main.py` and `app.py` share the same agent logic and tool registry. `main.py` is the command-line entry point; `app.py` wraps it in a streaming Streamlit UI.
