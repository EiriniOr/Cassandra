import subprocess


def shell_exec(command: str, confirm: bool = False) -> str:
    """Two-step shell execution. First call (confirm=False) returns dry-run.
    User confirms in chat, then model calls again with confirm=True to actually run.
    """
    if not confirm:
        return (
            f"DRY RUN — not executed: `{command}`\n\n"
            "Show this command to the user and ask if they want to run it. "
            "If yes, call shell_exec again with confirm=True."
        )
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=60
        )
        out = result.stdout
        err = result.stderr
        parts = [f"Exit code: {result.returncode}"]
        if out:
            parts.append(f"stdout:\n{out}")
        if err:
            parts.append(f"stderr:\n{err}")
        return "\n\n".join(parts)
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 60s"
    except Exception as exc:
        return f"Error: {exc}"


SCHEMA = {
    "name": "shell_exec",
    "description": (
        "Run a shell command. TWO-STEP: first call with confirm=False to dry-run "
        "and show the command to the user. After explicit user yes, call again with "
        "confirm=True to execute. Never set confirm=True without user approval first."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string"},
            "confirm": {
                "type": "boolean",
                "description": "Only set true after user has explicitly approved the command shown in dry-run.",
            },
        },
        "required": ["command"],
    },
}
