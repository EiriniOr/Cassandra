import { NextRequest, NextResponse } from "next/server";
import { searchLiterature } from "@/lib/research/search";
import { summarizeResults } from "@/lib/research/summarize";

export async function POST(req: NextRequest) {
  const { query, maxResults } = await req.json().catch(() => ({}) as { query?: unknown; maxResults?: unknown });
  if (typeof query !== "string" || !query.trim()) {
    return NextResponse.json({ error: "query is required" }, { status: 400 });
  }

  const { results, status } = await searchLiterature(query, {
    maxResults: typeof maxResults === "number" ? maxResults : undefined,
  });

  if (results.length === 0) {
    return NextResponse.json({ query, articles: [], unavailable: status.unavailable });
  }

  const articles = await summarizeResults(results, query);
  return NextResponse.json({ query, articles, unavailable: status.unavailable });
}
