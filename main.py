import anthropic
from dotenv import load_dotenv
from tools import TOOLS, TOOL_MAP

load_dotenv()

MODEL = "claude-opus-4-7"
client = anthropic.Anthropic()


def run_turn(messages: list) -> str:
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=8192,
            messages=messages,
            tools=TOOLS,
            thinking={"type": "adaptive"},
        )

        if response.stop_reason != "tool_use":
            return next((b.text for b in response.content if b.type == "text"), "")

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                fn = TOOL_MAP.get(block.name)
                result = fn(**block.input) if fn else f"Unknown tool: {block.name}"
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
