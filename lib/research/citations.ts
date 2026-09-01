// Portable citation formatting. Direct TS port of eirini-dash's
// app/tools/citations.py — deterministic post-processing so citations are
// never hallucinated by the model.

import type { Paper } from "./types";

function urlFor(result: Paper): string {
  if (result.url) return result.url;
  return result.doi ? `https://doi.org/${result.doi}` : "";
}

/** One clickable inline citation: `[[index]](url)` (plain `[index]` if no url). */
export function inlineLink(result: Paper): string {
  const url = urlFor(result);
  return url ? `[[${result.index}]](${url})` : `[${result.index}]`;
}

/** A Markdown sources list, one linked line per result. */
export function sourcesBlock(results: Paper[], heading = "Sources"): string {
  const lines = [`**${heading}**`];
  for (const r of results) {
    const url = urlFor(r);
    const authors = r.authors.slice(0, 3).join(", ") || "—";
    const label = `${authors} (${r.year ?? "n.d."}). ${r.title || "(untitled)"}. ${r.venue ?? ""}`.trim();
    lines.push(`[${r.index}] ` + (url ? `[${label}](${url})` : label));
  }
  return lines.join("\n");
}

/**
 * Rewrite bare inline `[n]` markers into `[[n]](url)` using the results.
 * Leaves already-linked `[[n]](…)` untouched. Independent of prompt/model.
 */
export function linkify(text: string, results: Paper[]): string {
  const byIndex = new Map<number, string>();
  for (const r of results) {
    const url = urlFor(r);
    if (r.index && url) byIndex.set(r.index, url);
  }
  return text.replace(/(?<!\[)\[(\d+)\](?!\()/g, (match, n) => {
    const url = byIndex.get(Number(n));
    return url ? `[[${n}]](${url})` : match;
  });
}
