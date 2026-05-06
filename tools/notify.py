import subprocess


def macos_notify(title: str, message: str, sound: bool = False) -> str:
    """Send a macOS notification via osascript."""
    safe_title = title.replace('"', '\\"')
    safe_message = message.replace('"', '\\"')
    script = f'display notification "{safe_message}" with title "{safe_title}"'
    if sound:
        script += ' sound name "Submarine"'
    try:
        subprocess.run(["osascript", "-e", script], timeout=5, check=True)
        return f"Notification sent: {title}"
    except Exception as exc:
        return f"Error: {exc}"


SCHEMA = {
    "name": "macos_notify",
    "description": "Send a macOS desktop notification. Use to ping the user when finishing a long task.",
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "message": {"type": "string"},
            "sound": {"type": "boolean", "description": "Play notification sound"},
        },
        "required": ["title", "message"],
    },
}
