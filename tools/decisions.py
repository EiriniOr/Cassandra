import re
from datetime import datetime
from pathlib import Path

DECISIONS_FILE = Path.home() / "cassandra-memory" / "decisions.md"


def _ensure():
    DECISIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DECISIONS_FILE.exists():
        DECISIONS_FILE.write_text("# Decision Journal\n\n")


def log_decision(decision: str, reasoning: str, expected_outcome: str = "") -> str:
    _ensure()
    stamp = datetime.now().strftime("%Y-%m-%d")
    block = f"\n## {stamp} — {decision}\n\n**Reasoning:** {reasoning}\n"
    if expected_outcome:
        block += f"\n**Expected outcome:** {expected_outcome}\n"
    block += "\n**Actual outcome:** _(fill in later)_\n"
    with DECISIONS_FILE.open("a") as f:
        f.write(block)
    return f"Logged decision dated {stamp}"


def recall_decisions(query: str = "") -> str:
    _ensure()
    text = DECISIONS_FILE.read_text()
    if not query:
        return text
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    blocks = re.split(r"\n(?=## )", text)
    matches = [b for b in blocks if pattern.search(b)]
    return "\n\n".join(matches) if matches else f"No decisions matching '{query}'"


LOG_SCHEMA = {
    "name": "log_decision",
    "description": "Append a decision to the decision journal with reasoning and expected outcome.",
    "input_schema": {
        "type": "object",
        "properties": {
            "decision": {
                "type": "string",
                "description": "Short label for the decision",
            },
            "reasoning": {
                "type": "string",
                "description": "Why this was chosen over alternatives",
            },
            "expected_outcome": {
                "type": "string",
                "description": "What success would look like",
            },
        },
        "required": ["decision", "reasoning"],
    },
}

RECALL_SCHEMA = {
    "name": "recall_decisions",
    "description": "Retrieve past decisions, optionally filtered by query. Empty query returns the full journal.",
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
    },
}
