import subprocess
from pathlib import Path


def _run(repo_path: str, args: list[str], timeout: int = 10) -> str:
    repo = Path(repo_path).expanduser().resolve()
    if not (repo / ".git").exists():
        return f"Error: {repo} is not a git repository"
    try:
        result = subprocess.run(
            ["git", "-C", str(repo)] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0 and not result.stdout:
            return f"Error: {result.stderr.strip()}"
        return result.stdout or "(empty)"
    except subprocess.TimeoutExpired:
        return "Error: git command timed out"
    except Exception as exc:
        return f"Error: {exc}"


def git_status(repo_path: str) -> str:
    return _run(repo_path, ["status", "--short", "--branch"])


def git_log(repo_path: str, n: int = 10) -> str:
    return _run(repo_path, ["log", f"-{n}", "--oneline", "--graph", "--decorate"])


def git_diff(repo_path: str, file: str = "", staged: bool = False) -> str:
    args = ["diff"]
    if staged:
        args.append("--staged")
    if file:
        args.extend(["--", file])
    return _run(repo_path, args)


STATUS_SCHEMA = {
    "name": "git_status",
    "description": "Run git status on a repo.",
    "input_schema": {
        "type": "object",
        "properties": {"repo_path": {"type": "string"}},
        "required": ["repo_path"],
    },
}

LOG_SCHEMA = {
    "name": "git_log",
    "description": "Show recent commits in a repo.",
    "input_schema": {
        "type": "object",
        "properties": {
            "repo_path": {"type": "string"},
            "n": {"type": "integer", "description": "Number of commits (default 10)"},
        },
        "required": ["repo_path"],
    },
}

DIFF_SCHEMA = {
    "name": "git_diff",
    "description": "Show working-tree or staged diff.",
    "input_schema": {
        "type": "object",
        "properties": {
            "repo_path": {"type": "string"},
            "file": {"type": "string", "description": "Optional path to filter"},
            "staged": {"type": "boolean", "description": "Show staged diff instead"},
        },
        "required": ["repo_path"],
    },
}
