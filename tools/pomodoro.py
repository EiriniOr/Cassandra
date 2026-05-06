"""Pomodoro = time management technique. 25-min focused work blocks separated
by 5-min breaks. Cassandra logs sessions to ~/cassandra-memory/time-tracker.json
so you can review where the day went.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

TRACKER = Path.home() / "cassandra-memory" / "time-tracker.json"


def _load() -> dict:
    if not TRACKER.exists():
        return {"current": None, "sessions": []}
    return json.loads(TRACKER.read_text())


def _save(data: dict):
    TRACKER.parent.mkdir(parents=True, exist_ok=True)
    TRACKER.write_text(json.dumps(data, indent=2))


def pomodoro_start(task: str, minutes: int = 25) -> str:
    data = _load()
    if data["current"]:
        return f"Already tracking '{data['current']['task']}' since {data['current']['started']}. Stop it first."
    data["current"] = {
        "task": task,
        "started": datetime.now().isoformat(timespec="seconds"),
        "target_minutes": minutes,
    }
    _save(data)
    end = datetime.now() + timedelta(minutes=minutes)
    return f"Started '{task}'. Target finish: {end.strftime('%H:%M')}"


def pomodoro_stop(notes: str = "") -> str:
    data = _load()
    if not data["current"]:
        return "Not currently tracking anything."
    cur = data["current"]
    started = datetime.fromisoformat(cur["started"])
    duration = (datetime.now() - started).total_seconds() / 60
    cur["ended"] = datetime.now().isoformat(timespec="seconds")
    cur["actual_minutes"] = round(duration, 1)
    if notes:
        cur["notes"] = notes
    data["sessions"].append(cur)
    data["current"] = None
    _save(data)
    return f"Stopped '{cur['task']}'. Duration: {cur['actual_minutes']} min"


def pomodoro_summary(date: str = "") -> str:
    data = _load()
    target = date or datetime.now().strftime("%Y-%m-%d")
    todays = [s for s in data["sessions"] if s["started"].startswith(target)]
    if not todays:
        return f"No sessions on {target}."
    total = sum(s.get("actual_minutes", 0) for s in todays)
    lines = [f"Sessions on {target} (total {total:.0f} min):\n"]
    for s in todays:
        start_t = s["started"][11:16]
        end_t = s.get("ended", "")[11:16] or "now"
        lines.append(
            f"  {start_t}–{end_t}  {s.get('actual_minutes', '?')} min  {s['task']}"
        )
        if s.get("notes"):
            lines.append(f"    note: {s['notes']}")
    if data["current"]:
        c = data["current"]
        lines.append(f"\n  IN PROGRESS since {c['started'][11:16]}: {c['task']}")
    return "\n".join(lines)


START_SCHEMA = {
    "name": "pomodoro_start",
    "description": "Start a focused work session (default 25 min). Records start time.",
    "input_schema": {
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "What you're working on"},
            "minutes": {
                "type": "integer",
                "description": "Target duration (default 25)",
            },
        },
        "required": ["task"],
    },
}

STOP_SCHEMA = {
    "name": "pomodoro_stop",
    "description": "Stop the current work session. Optionally add notes.",
    "input_schema": {
        "type": "object",
        "properties": {"notes": {"type": "string"}},
    },
}

SUMMARY_SCHEMA = {
    "name": "pomodoro_summary",
    "description": "Show all sessions for a date (default today).",
    "input_schema": {
        "type": "object",
        "properties": {
            "date": {"type": "string", "description": "YYYY-MM-DD; default today"}
        },
    },
}
