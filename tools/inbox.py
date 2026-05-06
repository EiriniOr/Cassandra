from datetime import datetime
from pathlib import Path

INBOX = Path.home() / "cassandra-memory" / "inbox.md"


def brain_dump(text: str) -> str:
    INBOX.parent.mkdir(parents=True, exist_ok=True)
    if not INBOX.exists():
        INBOX.write_text(
            "# Inbox\n\nQuick capture for half-formed thoughts. Triage later.\n\n"
        )
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with INBOX.open("a") as f:
        f.write(f"\n## {stamp}\n\n{text}\n")
    return f"Captured to inbox at {stamp}"


def inbox_read() -> str:
    if not INBOX.exists():
        return "Inbox is empty."
    return INBOX.read_text()


DUMP_SCHEMA = {
    "name": "brain_dump",
    "description": "Capture a half-formed thought to the inbox with timestamp. Triage later.",
    "input_schema": {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    },
}

READ_SCHEMA = {
    "name": "inbox_read",
    "description": "Read the entire inbox.",
    "input_schema": {"type": "object", "properties": {}},
}
