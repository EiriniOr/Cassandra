"""Cassandra web server — FastAPI + SSE streaming.

Local-only by default (binds to 127.0.0.1). Run with:
    python server.py
or:
    uvicorn server:app --host 127.0.0.1 --port 8000
"""

import json
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from shared import MODEL, SYSTEM
from tools import TOOL_MAP, TOOLS

load_dotenv()

app = FastAPI(title="Cassandra")
client = anthropic.Anthropic()

STATIC_DIR = Path(__file__).parent / "static"


class ChatRequest(BaseModel):
    messages: list


def _serialize_tool_block(block):
    """Anthropic content blocks → JSON-safe dict for storage in api_msgs."""
    if block.type == "text":
        return {"type": "text", "text": block.text}
    if block.type == "tool_use":
        return {
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": block.input,
        }
    if block.type == "thinking":
        return {
            "type": "thinking",
            "thinking": block.thinking,
            "signature": block.signature,
        }
    return {"type": block.type}


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.post("/api/chat")
def chat(req: ChatRequest):
    def gen():
        api_msgs = list(req.messages)
        try:
            while True:
                final = None
                with client.messages.stream(
                    model=MODEL,
                    max_tokens=8192,
                    system=SYSTEM,
                    messages=api_msgs,
                    tools=TOOLS,
                    thinking={"type": "adaptive"},
                ) as stream:
                    for chunk in stream.text_stream:
                        yield _sse("text", {"text": chunk})
                    final = stream.get_final_message()

                if final.stop_reason == "pause_turn":
                    api_msgs.append(
                        {
                            "role": "assistant",
                            "content": [
                                _serialize_tool_block(b) for b in final.content
                            ],
                        }
                    )
                    continue

                if final.stop_reason != "tool_use":
                    yield _sse("done", {})
                    return

                tool_results = []
                for block in final.content:
                    if block.type != "tool_use":
                        continue
                    yield _sse(
                        "tool_use",
                        {"id": block.id, "name": block.name, "input": block.input},
                    )
                    fn = TOOL_MAP.get(block.name)
                    if not fn:
                        result = f"Unknown tool: {block.name}"
                    else:
                        try:
                            result = fn(**block.input)
                        except Exception as exc:
                            result = f"Error: {exc}"
                    yield _sse(
                        "tool_result", {"id": block.id, "result": str(result)[:8000]}
                    )
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        }
                    )

                api_msgs.append(
                    {
                        "role": "assistant",
                        "content": [_serialize_tool_block(b) for b in final.content],
                    }
                )
                api_msgs.append({"role": "user", "content": tool_results})
                yield _sse("text_break", {})

        except anthropic.AuthenticationError:
            yield _sse(
                "error",
                {"message": "Invalid ANTHROPIC_API_KEY. Check your .env file."},
            )
        except Exception as exc:
            yield _sse("error", {"message": f"{type(exc).__name__}: {exc}"})

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/api/tools")
def list_tools():
    return {"tools": [{"name": t.get("name"), "schema": t} for t in TOOLS]}


# Static routes — serve the SPA-ish frontend
@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/tools")
def tools_page():
    return FileResponse(STATIC_DIR / "tools.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
