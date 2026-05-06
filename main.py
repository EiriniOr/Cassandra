import anthropic
from dotenv import load_dotenv

from tools import TOOL_MAP, TOOLS

load_dotenv()

MODEL = "claude-opus-4-7"

SYSTEM = """You are Cassandra, a personal AI agent for Eirini. You have access to:

- Web search and fetch (Anthropic-hosted)
- A persistent memory wiki at ~/cassandra-memory/ following Karpathy's LLM Wiki
  pattern. Read ~/cassandra-memory/CLAUDE.md to learn the schema. When the user
  asks about prior context, search memory FIRST. When they share something
  worth remembering, ingest it: write a source page, update entities/concepts,
  append to log.md.
- File read/write (general filesystem)
- Calculator, clipboard, macOS notifications
- Project picker (scans ~/ for git repos)
- Decision journal, brain dump inbox
- Shell execution (TWO-STEP — always show command first, get user yes, then
  call again with confirm=true)
- Git inspector (status, log, diff)
- Pomodoro time tracker
- Knowledge fetchers: arXiv, Hacker News, save_article (drops sources into
  the memory raw/ dir for later wiki ingestion)
- Tarot draw (for fun)

Be concise. Use tools when they actually help."""

client = anthropic.Anthropic()


def run_turn(messages: list) -> str:
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=8192,
            system=SYSTEM,
            messages=messages,
            tools=TOOLS,
            thinking={"type": "adaptive"},
        )

        if response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            continue

        if response.stop_reason != "tool_use":
            return next((b.text for b in response.content if b.type == "text"), "")

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                fn = TOOL_MAP.get(block.name)
                if not fn:
                    result = f"Unknown tool: {block.name}"
                else:
                    try:
                        result = fn(**block.input)
                    except Exception as exc:
                        result = f"Error executing {block.name}: {exc}"
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    }
                )
        messages.append({"role": "user", "content": tool_results})


def main():
    print("Cassandra — AI Agent (type 'quit' to exit)\n")
    messages = []

    sample = "What can you help me with today?"
    print(f"You: {sample}")
    messages.append({"role": "user", "content": sample})
    reply = run_turn(messages)
    messages.append({"role": "assistant", "content": reply})
    print(f"Cassandra: {reply}\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue
        messages.append({"role": "user", "content": user_input})
        reply = run_turn(messages)
        messages.append({"role": "assistant", "content": reply})
        print(f"Cassandra: {reply}\n")


if __name__ == "__main__":
    main()
