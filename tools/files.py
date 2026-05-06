from pathlib import Path


def _resolve(path: str) -> Path:
    return Path(path).expanduser().resolve()


def file_read(path: str, max_chars: int = 50000) -> str:
    p = _resolve(path)
    if not p.exists():
        return f"Error: {p} does not exist"
    if not p.is_file():
        return f"Error: {p} is not a file"
    text = p.read_text(errors="replace")
    if len(text) > max_chars:
        return (
            text[:max_chars]
            + f"\n\n[truncated at {max_chars} chars; total {len(text)}]"
        )
    return text


def file_write(path: str, content: str, append: bool = False) -> str:
    p = _resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with p.open(mode) as f:
        f.write(content)
    return f"{'Appended to' if append else 'Wrote'} {p} ({len(content)} chars)"


def file_list(path: str, recursive: bool = False) -> str:
    p = _resolve(path)
    if not p.exists():
        return f"Error: {p} does not exist"
    if p.is_file():
        return str(p)
    items = sorted(p.rglob("*") if recursive else p.iterdir())
    return (
        "\n".join(str(i.relative_to(p)) + ("/" if i.is_dir() else "") for i in items)
        or "(empty)"
    )


READ_SCHEMA = {
    "name": "file_read",
    "description": "Read a text file from disk. Paths are expanded (~ supported).",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path"},
            "max_chars": {
                "type": "integer",
                "description": "Truncate output (default 50000)",
            },
        },
        "required": ["path"],
    },
}

WRITE_SCHEMA = {
    "name": "file_write",
    "description": "Write or append text to a file. Creates parent dirs.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
            "append": {
                "type": "boolean",
                "description": "Append instead of overwrite (default false)",
            },
        },
        "required": ["path", "content"],
    },
}

LIST_SCHEMA = {
    "name": "file_list",
    "description": "List files in a directory.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "recursive": {"type": "boolean", "description": "Recurse into subdirs"},
        },
        "required": ["path"],
    },
}
