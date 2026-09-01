import { NextRequest, NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { MODEL, SYSTEM_PROMPT } from "@/lib/prompt";
import { searchLiterature } from "@/lib/research/search";
import { summarizeResults } from "@/lib/research/summarize";
import type { ArticlePresentation } from "@/lib/research/summarize";

const client = new Anthropic();

const SEARCH_TOOL: Anthropic.Tool = {
  name: "search_literature",
  description:
    "Search scientific literature (OpenAlex + arXiv) for a research topic. Always use this when the user wants sources, papers, or evidence — never invent citations yourself.",
  input_schema: {
    type: "object",
    properties: {
      query: { type: "string", description: "The research topic or question to search for." },
      maxResults: { type: "number", description: "Max number of results (default 6, max 25)." },
    },
    required: ["query"],
  },
};

const MAX_TOOL_ROUNDS = 3;

export async function POST(req: NextRequest) {
  const body = (await req.json().catch(() => null)) as {
    question?: unknown;
    history?: unknown;
  } | null;

  if (!body || typeof body.question !== "string" || !body.question.trim()) {
    return NextResponse.json({ error: "question is required" }, { status: 400 });
  }

  const messages: Anthropic.MessageParam[] = [
    ...(Array.isArray(body.history) ? (body.history as Anthropic.MessageParam[]) : []),
    { role: "user", content: body.question },
  ];

  let facts: ArticlePresentation[] = [];
  let unavailable: string[] = [];

  for (let round = 0; round < MAX_TOOL_ROUNDS; round++) {
    const res = await client.messages.create({
      model: MODEL,
      max_tokens: 1500,
      system: SYSTEM_PROMPT,
      tools: [SEARCH_TOOL],
      messages,
    });

    const toolUse = res.content.find(
      (b): b is Anthropic.ToolUseBlock => b.type === "tool_use",
    );

    if (!toolUse) {
      const text = res.content.find((b) => b.type === "text")?.text?.trim();
      const answerText =
        text || (res.stop_reason === "refusal" ? "Claude declined to answer this question." : "");
      messages.push({ role: "assistant", content: res.content });
      return NextResponse.json({ answerText, facts, unavailable, history: messages });
    }

    messages.push({ role: "assistant", content: res.content });

    const args = toolUse.input as { query: string; maxResults?: number };
    const { results, status } = await searchLiterature(args.query, { maxResults: args.maxResults });
    unavailable = status.unavailable;
    facts = results.length > 0 ? await summarizeResults(results, args.query) : [];

    messages.push({
      role: "user",
      content: [
        {
          type: "tool_result",
          tool_use_id: toolUse.id,
          content: JSON.stringify({ query: args.query, articles: facts, unavailable }),
        },
      ],
    });
  }

  return NextResponse.json({ error: "Too many tool calls in one turn" }, { status: 500 });
}
