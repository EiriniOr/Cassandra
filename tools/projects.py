import subprocess
from pathlib import Path

HOME = Path.home()


def project_picker(min_files: int = 3) -> str:
    """Scan ~/* for git repos, sort by last commit time, return top suggestions."""
    results = []
    for entry in HOME.iterdir():
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        git_dir = entry / ".git"
        if not git_dir.exists():
            continue
        try:
            last = subprocess.run(
                ["git", "-C", str(entry), "log", "-1", "--format=%cr|%s"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if last.returncode != 0:
                continue
            rel_time, _, msg = last.stdout.strip().partition("|")
            status = subprocess.run(
                ["git", "-C", str(entry), "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            dirty = "*" if status.stdout.strip() else " "
            ts = subprocess.run(
                ["git", "-C", str(entry), "log", "-1", "--format=%ct"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            sort_key = int(ts.stdout.strip()) if ts.stdout.strip().isdigit() else 0
            results.append((sort_key, entry.name, rel_time, dirty, msg[:60]))
        except Exception:
            continue

    results.sort(reverse=True)
    if not results:
        return "No git repos found in home directory."
    lines = [
        f"{'*' if d.strip() else ' '} {name:<30} {rel:<20} {msg}"
        for _, name, rel, d, msg in results[:20]
    ]
    return (
        "Recent projects (sorted by last commit; * = uncommitted changes):\n\n"
        + "\n".join(lines)
    )


SCHEMA = {
    "name": "project_picker",
    "description": "Scan ~/ for git repos and list them sorted by last commit time. Helps decide what to work on next.",
    "input_schema": {"type": "object", "properties": {}},
}
