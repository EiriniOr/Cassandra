import subprocess


def clipboard_read() -> str:
    try:
        result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
        return result.stdout
    except Exception as exc:
        return f"Error: {exc}"


def clipboard_write(text: str) -> str:
    try:
        subprocess.run(["pbcopy"], input=text, text=True, timeout=5, check=True)
        return f"Copied {len(text)} chars to clipboard"
    except Exception as exc:
        return f"Error: {exc}"


READ_SCHEMA = {
    "name": "clipboard_read",
    "description": "Read the macOS clipboard contents.",
    "input_schema": {"type": "object", "properties": {}},
}

WRITE_SCHEMA = {
    "name": "clipboard_write",
    "description": "Write text to the macOS clipboard.",
    "input_schema": {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    },
}
