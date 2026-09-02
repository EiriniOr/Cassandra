// Progressive-disclosure summaries: one Claude call per paper producing a
// one-sentence fact + a fuller paragraph, grounded in the real article body
// when an open-access PDF is available (falls back to the abstract). Both
// levels are generated up front so the ArticleCard's zoom is instant.

import Anthropic from "@anthropic-ai/sdk";
import type { Paper } from "./types";
import { fetchFulltext, relevantPassages } from "./fulltext";

const client = new Anthropic();
const SUMMARY_MODEL = process.env.CASSANDRA_FAST_MODEL || "claude-haiku-4-5";

export interface ArticlePresentation extends Paper {
  sentence: string;
  paragraph: string;
  /** Real, verified open-access PDF URL — null if the article isn't OA. */
  pdfUrl: string | null;
}

async function summarizeOne(
  paper: Paper,
  query: string,
  groundingText: string,
): Promise<{ relevant: boolean; sentence: string; paragraph: string }> {
  const source = groundingText
    ? `Excerpt from the actual article body:\n${groundingText}`
    : `Abstract: ${paper.abstractSnippet ?? "(none available)"}`;

  const prompt = `Paper: "${paper.title}" (${paper.authors.slice(0, 3).join(", ") || "unknown authors"}, ${paper.year ?? "n.d."})
${source}

Research topic: "${query}"

First judge relevance: does this paper actually address the topic, or does it
just share keywords while covering something else (or only mention the topic
in passing)? Be strict — if it's tangential, mark it not relevant.

If relevant, write:
1. "sentence": one factual sentence (<= 25 words) stating the paper's single most relevant finding for this topic.
2. "paragraph": a 3-5 sentence paragraph expanding on it, grounded ONLY in the text above — no claims beyond it.
If not relevant, leave "sentence" and "paragraph" as empty strings.

Respond with ONLY compact JSON: {"relevant": true|false, "sentence": "...", "paragraph": "..."}`;

  const res = await client.messages.create({
    model: SUMMARY_MODEL,
    max_tokens: 400,
    messages: [{ role: "user", content: prompt }],
  });
  const text = res.content.find((b) => b.type === "text")?.text ?? "{}";
  try {
    const jsonStart = text.indexOf("{");
    const jsonEnd = text.lastIndexOf("}");
    const parsed = JSON.parse(text.slice(jsonStart, jsonEnd + 1));
    const sentence = String(parsed.sentence ?? "").trim() || paper.title;
    return {
      relevant: parsed.relevant !== false,
      sentence,
      paragraph: String(parsed.paragraph ?? "").trim() || paper.abstractSnippet || sentence,
    };
  } catch {
    return { relevant: true, sentence: paper.title, paragraph: paper.abstractSnippet ?? "" };
  }
}

export async function summarizeResults(
  papers: Paper[],
  query: string,
): Promise<ArticlePresentation[]> {
  const presented = await Promise.all(
    papers.map(async (paper) => {
      const { text: fulltext, pdfUrl } = await fetchFulltext(paper.url, paper.doi);
      const grounding = fulltext ? relevantPassages(fulltext, query, 3).join("\n\n") : "";
      const { relevant, sentence, paragraph } = await summarizeOne(paper, query, grounding);
      if (!relevant) return null;
      return { ...paper, sentence, paragraph, pdfUrl };
    }),
  );
  return presented.filter((a): a is ArticlePresentation => a !== null);
}
