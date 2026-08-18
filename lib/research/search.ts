// Scientific literature search — OpenAlex + arXiv, merged and de-duplicated.
// TS port of eirini-dash's app/tools/scientific_search.py (same two sources,
// same dedupe-by-DOI-or-title, same concurrent link validation before results
// reach the model, same polite-pool User-Agent pattern).

import { XMLParser } from "fast-xml-parser";
import type { Paper, SearchStatus } from "./types";

const OPENALEX_URL = "https://api.openalex.org/works";
const ARXIV_URL = "https://export.arxiv.org/api/query";
const HTTP_TIMEOUT_MS = 20_000;
const UA = "Cassandra/0.1 (personal research assistant; mailto:renaorn@gmail.com)";

async function fetchWithTimeout(
  url: string,
  init: RequestInit = {},
  timeoutMs = HTTP_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal, headers: { "User-Agent": UA, ...init.headers } });
  } finally {
    clearTimeout(timer);
  }
}

async function getRetry(url: string, attempts = 3): Promise<Response> {
  let delay = 1000;
  let last: Response | null = null;
  for (let i = 0; i < attempts; i++) {
    const res = await fetchWithTimeout(url);
    if ((res.status === 429 || res.status === 503) && i < attempts - 1) {
      await new Promise((r) => setTimeout(r, Math.min(delay, 3000)));
      delay *= 2;
      last = res;
      continue;
    }
    return res;
  }
  return last!;
}

function cleanDoi(doi: string | null | undefined): string | null {
  if (!doi) return null;
  const cleaned = doi.replace("https://doi.org/", "").replace("http://doi.org/", "").trim();
  return cleaned || null;
}

function snippet(text: string | null | undefined, limit = 320): string | null {
  if (!text) return null;
  const collapsed = text.split(/\s+/).join(" ");
  return collapsed.length <= limit ? collapsed : collapsed.slice(0, limit).trimEnd() + "…";
}

function reconstructAbstract(invertedIndex: Record<string, number[]> | null | undefined): string | null {
  if (!invertedIndex) return null;
  const positions: [number, string][] = [];
  for (const [word, idxs] of Object.entries(invertedIndex)) {
    for (const i of idxs) positions.push([i, word]);
  }
  positions.sort((a, b) => a[0] - b[0]);
  const text = positions.map(([, w]) => w).join(" ");
  return text || null;
}

async function searchOpenAlex(
  query: string,
  maxResults: number,
  mailto: string,
  unavailable: Set<string>,
  apiKey: string,
): Promise<Paper[]> {
  const params = new URLSearchParams({
    search: query,
    per_page: String(maxResults),
    select: "title,authorships,publication_year,primary_location,doi,open_access,abstract_inverted_index",
  });
  if (mailto) params.set("mailto", mailto);
  if (apiKey) params.set("api_key", apiKey);

  let data: any;
  try {
    const res = await getRetry(`${OPENALEX_URL}?${params}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch {
    unavailable.add("OpenAlex");
    return [];
  }

  const papers: Paper[] = [];
  for (const work of data.results ?? []) {
    const authors: string[] = (work.authorships ?? [])
      .map((a: any) => a.author?.display_name)
      .filter(Boolean);
    const location = work.primary_location ?? {};
    const source = location.source ?? {};
    const doi = cleanDoi(work.doi);
    const oa = work.open_access ?? {};
    let url: string | null = oa.oa_url || location.landing_page_url || null;
    if (!url && doi) url = `https://doi.org/${doi}`;
    const abstract = reconstructAbstract(work.abstract_inverted_index);
    papers.push({
      index: 0,
      title: work.title || "(untitled)",
      authors,
      year: work.publication_year ?? null,
      venue: source.display_name ?? null,
      doi,
      url,
      abstractSnippet: snippet(abstract),
      source: "openalex",
      linkOk: true,
    });
  }
  return papers;
}

async function searchArxiv(
  query: string,
  maxResults: number,
  unavailable: Set<string>,
): Promise<Paper[]> {
  const params = new URLSearchParams({
    search_query: `all:${query}`,
    start: "0",
    max_results: String(maxResults),
    sortBy: "relevance",
    sortOrder: "descending",
  });

  let xml: string;
  try {
    const res = await getRetry(`${ARXIV_URL}?${params}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    xml = await res.text();
  } catch {
    unavailable.add("arXiv");
    return [];
  }

  const parser = new XMLParser({ ignoreAttributes: false, attributeNamePrefix: "@_" });
  const feed = parser.parse(xml);
  const rawEntries = feed?.feed?.entry;
  const entries = Array.isArray(rawEntries) ? rawEntries : rawEntries ? [rawEntries] : [];

  const papers: Paper[] = [];
  for (const entry of entries) {
    const title = String(entry.title ?? "").trim();
    const summaryText = String(entry.summary ?? "").trim();
    const published = String(entry.published ?? "");
    const year = /^\d{4}/.test(published) ? Number(published.slice(0, 4)) : null;

    const authorField = entry.author;
    const authorList = Array.isArray(authorField) ? authorField : authorField ? [authorField] : [];
    const authors: string[] = authorList
      .map((a: any) => String(a?.name ?? "").trim())
      .filter(Boolean);

    const linkField = entry.link;
    const links = Array.isArray(linkField) ? linkField : linkField ? [linkField] : [];
    const altLink = links.find((l: any) => l?.["@_rel"] === "alternate");
    const url = altLink?.["@_href"] ?? null;
    const doi = cleanDoi(entry["arxiv:doi"]);

    papers.push({
      index: 0,
      title: title || "(untitled)",
      authors,
      year,
      venue: "arXiv preprint",
      doi,
      url,
      abstractSnippet: snippet(summaryText),
      source: "arxiv",
      linkOk: true,
    });
  }
  return papers;
}

function dedupe(papers: Paper[]): Paper[] {
  const seen = new Set<string>();
  const out: Paper[] = [];
  for (const p of papers) {
    const key = (p.doi || "").toLowerCase() || (p.title || "").toLowerCase().trim();
    if (!key || seen.has(key)) continue;
    seen.add(key);
    out.push(p);
  }
  return out;
}

async function checkLinkOk(url: string): Promise<boolean> {
  try {
    let res = await fetchWithTimeout(url, { method: "HEAD", redirect: "follow" }, 6000);
    if (res.status < 400) return true;
    if ([403, 405, 501].includes(res.status)) {
      res = await fetchWithTimeout(url, { method: "GET", redirect: "follow" }, 6000);
      return res.status < 400;
    }
    return false;
  } catch {
    return false;
  }
}

async function validateLinks(papers: Paper[]): Promise<void> {
  await Promise.all(
    papers.map(async (p) => {
      const candidates: string[] = [];
      if (p.doi) candidates.push(`https://doi.org/${p.doi}`);
      if (p.url && !candidates.includes(p.url)) candidates.push(p.url);
      for (const url of candidates) {
        if (await checkLinkOk(url)) {
          p.url = url;
          p.linkOk = true;
          return;
        }
      }
      p.url = candidates[0] ?? null;
      p.linkOk = false;
    }),
  );
}

export interface SearchOptions {
  maxResults?: number;
  includeArxiv?: boolean;
  mailto?: string;
  validateLinks?: boolean;
  apiKey?: string;
}

/**
 * Search scientific literature and return merged, de-duplicated results.
 * Empty list if nothing is found — callers must say so rather than invent sources.
 */
export async function searchLiterature(
  query: string,
  opts: SearchOptions = {},
): Promise<{ results: Paper[]; status: SearchStatus }> {
  const n = Math.max(1, Math.min(opts.maxResults ?? 6, 25));
  const unavailable = new Set<string>();
  const mailto = opts.mailto ?? "renaorn@gmail.com";

  let results = await searchOpenAlex(query, n, mailto, unavailable, opts.apiKey ?? "");
  if (opts.includeArxiv ?? true) {
    results = results.concat(await searchArxiv(query, Math.max(2, Math.floor(n / 2)), unavailable));
  }
  results = dedupe(results).slice(0, n);
  if (opts.validateLinks ?? true) {
    await validateLinks(results);
  }
  results.forEach((p, i) => {
    p.index = i + 1;
  });
  return { results, status: { unavailable: Array.from(unavailable).sort() } };
}
