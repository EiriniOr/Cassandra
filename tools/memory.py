"""Karpathy's LLM Wiki pattern: agent maintains a structured markdown wiki.

Folder layout (auto-initialized at ~/cassandra-memory/):
    raw/                    immutable source dump
    wiki/
        index.md           master catalog
        log.md             chronological activity record
        entities/          people, orgs, products
        concepts/          ideas, frameworks, theories
        sources/           one-page summary per source
        synthesis/         cross-cutting analyses
    CLAUDE.md              schema/instructions for the agent

See: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
"""

import re
from datetime import datetime
from pathlib import Path

MEMORY = Path.home() / "cassandra-memory"

SCHEMA_DOC = """# Cassandra Memory Schema

Maintained by Cassandra (an AI agent) following Karpathy's LLM Wiki pattern.

## Layout

- `raw/` — immutable source dump. Articles, transcripts, notes, screenshots.
- `wiki/` — LLM-organized markdown.
  - `index.md` — master catalog of all wiki pages.
  - `log.md` — chronological activity record. Append every ingest/significant query.
  - `entities/` — people, organizations, products. One file per entity.
  - `concepts/` — ideas, frameworks, theories. One file per concept.
  - `sources/` — one-page summary per source dropped in `raw/`.
  - `synthesis/` — cross-cutting analyses across multiple entities/concepts.

## Page Format

Every wiki page starts with frontmatter:

```
---
title: <title>
type: entity | concept | source | synthesis
tags: [tag1, tag2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

Body uses `[[wiki-link]]` for cross-references and `## Sources` at the bottom
listing files from `raw/`.

## Workflows

**Ingest** — when a new file lands in `raw/`:
1. Read it.
2. Write a summary page in `wiki/sources/<slug>.md`.
3. Update or create relevant `entities/` and `concepts/` pages.
4. Append a line to `log.md`: `YYYY-MM-DD - ingested <filename>`.
5. Refresh `index.md` if new top-level pages were created.

**Query** — when answering from memory:
1. Search wiki pages first (`memory_search`).
2. Synthesize answer.
3. If the answer was non-trivial, file it back into `synthesis/` for next time.

**Lint** — periodically check for:
- Orphan pages (no inbound `[[links]]`)
- Broken `[[links]]`
- Stale claims (contradicted by newer sources)
- Missing entries in `index.md`
"""


def _ensure_init():
    if MEMORY.exists():
        return
    MEMORY.mkdir(parents=True)
    (MEMORY / "raw").mkdir()
    wiki = MEMORY / "wiki"
    wiki.mkdir()
    for sub in ("entities", "concepts", "sources", "synthesis"):
        (wiki / sub).mkdir()
    (wiki / "index.md").write_text(
        "# Index\n\nMaster catalog of wiki pages. Maintained by Cassandra.\n\n## Entities\n\n## Concepts\n\n## Sources\n\n## Synthesis\n"
    )
    (wiki / "log.md").write_text("# Activity Log\n\n")
    (MEMORY / "CLAUDE.md").write_text(SCHEMA_DOC)


def _safe_path(rel: str) -> Path:
    p = (MEMORY / rel).resolve()
    if not str(p).startswith(str(MEMORY.resolve())):
        raise ValueError(f"Path escapes memory dir: {rel}")
    return p


def memory_read(path: str) -> str:
    _ensure_init()
    p = _safe_path(path)
    if not p.exists():
        return f"Error: {path} not found in memory"
    return p.read_text(errors="replace")


def memory_write(path: str, content: str) -> str:
    _ensure_init()
    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Wrote {path} ({len(content)} chars)"


def memory_list(subdir: str = "") -> str:
    _ensure_init()
    p = _safe_path(subdir) if subdir else MEMORY
    if not p.exists():
        return f"Error: {subdir} not found"
    items = sorted(p.rglob("*"))
    return "\n".join(
        str(i.relative_to(MEMORY)) + ("/" if i.is_dir() else "")
        for i in items
        if not i.name.startswith(".")
    )


def memory_search(query: str) -> str:
    _ensure_init()
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    hits = []
    for f in MEMORY.rglob("*.md"):
        try:
            text = f.read_text(errors="replace")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                hits.append(f"{f.relative_to(MEMORY)}:{i}: {line.strip()}")
                if len(hits) >= 100:
                    return "\n".join(hits) + "\n[truncated at 100]"
    return "\n".join(hits) if hits else f"No matches for '{query}'"


def memory_log(entry: str) -> str:
    _ensure_init()
    log = MEMORY / "wiki" / "log.md"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with log.open("a") as f:
        f.write(f"- {stamp} — {entry}\n")
    return f"Logged: {entry}"


READ_SCHEMA = {
    "name": "memory_read",
    "description": "Read a file from Cassandra's memory wiki (~/cassandra-memory/). Paths are relative to the memory root, e.g. 'wiki/index.md'.",
    "input_schema": {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    },
}

WRITE_SCHEMA = {
    "name": "memory_write",
    "description": "Write a markdown file to memory wiki. Use the schema in CLAUDE.md (frontmatter, [[wiki-links]]). Path is relative to memory root.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "e.g. 'wiki/entities/karpathy.md'",
            },
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    },
}

LIST_SCHEMA = {
    "name": "memory_list",
    "description": "List files in memory. Empty subdir lists everything.",
    "input_schema": {
        "type": "object",
        "properties": {
            "subdir": {
                "type": "string",
                "description": "e.g. 'wiki/entities' or '' for all",
            }
        },
    },
}

SEARCH_SCHEMA = {
    "name": "memory_search",
    "description": "Grep across all markdown files in memory. Use first when answering questions about prior context.",
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
}

LOG_SCHEMA = {
    "name": "memory_log",
    "description": "Append a timestamped entry to wiki/log.md. Use when ingesting sources or after non-trivial queries.",
    "input_schema": {
        "type": "object",
        "properties": {"entry": {"type": "string"}},
        "required": ["entry"],
    },
}
