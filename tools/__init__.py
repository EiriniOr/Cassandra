"""Cassandra tool registry.

TOOLS — list of tool definitions sent to the API. Mixes Anthropic-hosted
server tools (web_search, web_fetch — executed by Anthropic, no Python fn
needed) with local custom tools (everything else, dispatched via TOOL_MAP).

TOOL_MAP — name → callable for custom tools. Server tools are NOT in this
map; their results come back inline from Anthropic.
"""

from tools import (
    calculator,
    clipboard,
    decisions,
    files,
    git_tools,
    inbox,
    knowledge,
    memory,
    notify,
    pomodoro,
    projects,
    shell,
    tarot,
)

# Server-side tools — Anthropic executes these; no entry in TOOL_MAP.
SERVER_TOOLS = [
    {"type": "web_search_20260209", "name": "web_search"},
    {"type": "web_fetch_20260209", "name": "web_fetch"},
]

# Custom tools — schemas + dispatch table.
CUSTOM_SCHEMAS = [
    calculator.SCHEMA,
    files.READ_SCHEMA,
    files.WRITE_SCHEMA,
    files.LIST_SCHEMA,
    memory.READ_SCHEMA,
    memory.WRITE_SCHEMA,
    memory.LIST_SCHEMA,
    memory.SEARCH_SCHEMA,
    memory.LOG_SCHEMA,
    projects.SCHEMA,
    decisions.LOG_SCHEMA,
    decisions.RECALL_SCHEMA,
    inbox.DUMP_SCHEMA,
    inbox.READ_SCHEMA,
    clipboard.READ_SCHEMA,
    clipboard.WRITE_SCHEMA,
    shell.SCHEMA,
    git_tools.STATUS_SCHEMA,
    git_tools.LOG_SCHEMA,
    git_tools.DIFF_SCHEMA,
    notify.SCHEMA,
    pomodoro.START_SCHEMA,
    pomodoro.STOP_SCHEMA,
    pomodoro.SUMMARY_SCHEMA,
    knowledge.ARXIV_SCHEMA,
    knowledge.HN_SCHEMA,
    knowledge.SAVE_SCHEMA,
    tarot.SCHEMA,
]

TOOLS = SERVER_TOOLS + CUSTOM_SCHEMAS

TOOL_MAP = {
    "calculate": calculator.calculate,
    "file_read": files.file_read,
    "file_write": files.file_write,
    "file_list": files.file_list,
    "memory_read": memory.memory_read,
    "memory_write": memory.memory_write,
    "memory_list": memory.memory_list,
    "memory_search": memory.memory_search,
    "memory_log": memory.memory_log,
    "project_picker": projects.project_picker,
    "log_decision": decisions.log_decision,
    "recall_decisions": decisions.recall_decisions,
    "brain_dump": inbox.brain_dump,
    "inbox_read": inbox.inbox_read,
    "clipboard_read": clipboard.clipboard_read,
    "clipboard_write": clipboard.clipboard_write,
    "shell_exec": shell.shell_exec,
    "git_status": git_tools.git_status,
    "git_log": git_tools.git_log,
    "git_diff": git_tools.git_diff,
    "macos_notify": notify.macos_notify,
    "pomodoro_start": pomodoro.pomodoro_start,
    "pomodoro_stop": pomodoro.pomodoro_stop,
    "pomodoro_summary": pomodoro.pomodoro_summary,
    "arxiv_search": knowledge.arxiv_search,
    "hn_top": knowledge.hn_top,
    "save_article": knowledge.save_article,
    "tarot_draw": tarot.tarot_draw,
}
