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
    "Search scientific literature (OpenAlex + arXiv) for a research topic. Call this for every substantive question by default, not only when the user explicitly asks for papers or sources — never invent citations yourself.",
  input_schema: {
    type: "object",
    properties: {
      query: { type: "string", description: "The research topic or question to search for." },
      maxResults: { type: "number", description: "Max number of results (default 6, max 25)." },
    },
    required: ["query"],
  },
};

const MAX_TOOL_ROUNDS = 5;

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
      // Thinking blocks count against this budget too, so it needs real
      // headroom even though the visible answer itself is short — the
      // prompt's word-count rule controls length, not this cap.
      max_tokens: 1024,
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

  // The model kept calling the tool instead of committing to an answer —
  // force a final text-only turn from whatever context it's gathered so far
  // rather than surfacing a hard error for something the user can't act on.
  const final = await client.messages.create({
    model: MODEL,
    max_tokens: 1024,
    system: SYSTEM_PROMPT,
    tool_choice: { type: "none" },
    messages,
  });
  const finalText = final.content.find((b) => b.type === "text")?.text?.trim();
  messages.push({ role: "assistant", content: final.content });
  return NextResponse.json({
    answerText: finalText || "Couldn't settle on an answer for this one — try rephrasing?",
    facts,
    unavailable,
    history: messages,
  });
}
