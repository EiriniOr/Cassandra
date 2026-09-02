// Open-access full-text reading for grounded summaries. TS port of
// eirini-dash's app/tools/fulltext.py: resolve an OA PDF, extract text, and
// return passages most relevant to a query — so summaries can quote real
// article body text, not just the abstract. PyMuPDF -> unpdf (serverless-safe,
// no native deps).

import { extractText, getDocumentProxy } from "unpdf";

const UA = "Cassandra/1.0 (personal research assistant)";
const HTTP_TIMEOUT_MS = 30_000;

function arxivPdfUrl(url: string | null): string | null {
  if (!url) return null;
  const m = url.match(/arxiv\.org\/(?:abs|pdf)\/([\w.\-/]+?)(?:v\d+)?(?:\.pdf)?$/);
  return m ? `https://arxiv.org/pdf/${m[1]}` : null;
}

async function fetchTimeout(url: string, timeoutMs = HTTP_TIMEOUT_MS): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, {
      headers: { "User-Agent": UA },
      redirect: "follow",
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }
}

export interface FulltextResult {
  text: string;
  /** The exact URL that resolved to a real, working PDF — what the 3rd zoom level embeds. */
  pdfUrl: string | null;
}

/** Download an open-access PDF and return its extracted text + the URL that worked. */
export async function fetchFulltext(url: string | null, doi: string | null = null): Promise<FulltextResult> {
  const seen = new Set<string>();
  const queue: string[] = [];
  const enqueue = (u: string | null) => {
    if (u && !seen.has(u)) {
      seen.add(u);
      queue.push(u);
    }
  };

  enqueue(arxivPdfUrl(url));
  enqueue(url);
  if (doi) enqueue(`https://doi.org/${doi}`);

  while (queue.length > 0) {
    const u = queue.shift()!;
    let res: Response;
    try {
      res = await fetchTimeout(u);
    } catch {
      continue;
    }
    if (!res.ok) continue;

    // Some publishers (e.g. Springer) serve an access/cookie-consent notice
    // AS an actual valid PDF file at the expected URL, which passes every
    // format check below despite not being the article — the one reliable
    // tell is an "error=" param the redirect chain leaves in the final URL.
    try {
      if (new URL(res.url).searchParams.has("error")) continue;
    } catch {
      // res.url failed to parse as a URL — fall through to the normal checks
    }

    const contentType = res.headers.get("content-type") ?? "";
    const buf = new Uint8Array(await res.arrayBuffer());
    const isPdfMagic = buf[0] === 0x25 && buf[1] === 0x50 && buf[2] === 0x44 && buf[3] === 0x46; // %PDF
    const looksLikePdf = contentType.includes("pdf") || u.toLowerCase().endsWith(".pdf") || isPdfMagic;

    if (!looksLikePdf) {
      // A DOI or landing-page redirect (res.url) may resolve to an arXiv abstract
      // page rather than the PDF directly — try its PDF variant too.
      enqueue(arxivPdfUrl(res.url));
      continue;
    }

    try {
      const pdf = await getDocumentProxy(buf);
      const { text } = await extractText(pdf, { mergePages: true });
      // res.url reflects the post-redirect location (e.g. doi.org -> publisher PDF).
      if (text.length > 500) return { text, pdfUrl: res.url || u };
    } catch {
      continue;
    }
  }
  return { text: "", pdfUrl: null };
}

function passages(text: string, target = 900): string[] {
  const paras = text
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter((p) => p.length > 120);
  const out: string[] = [];
  let buf = "";
  for (const p of paras) {
    if (buf.length + p.length < target) {
      buf = (buf + " " + p).trim();
    } else {
      if (buf) out.push(buf);
      buf = p;
    }
  }
  if (buf) out.push(buf);
  return out;
}

/** Top-k passages by question-term overlap (lexical, instant). */
export function relevantPassages(text: string, query: string, k = 4): string[] {
  const ps = passages(text);
  if (ps.length === 0) return [];
  const terms = new Set(
    (query.toLowerCase().match(/[\p{L}\p{N}]+/gu) ?? []).filter((t) => t.length > 3),
  );

  function score(p: string): number {
    const pl = p.toLowerCase();
    let s = 0;
    for (const t of terms) s += pl.split(t).length - 1;
    return s;
  }

  const ranked = [...ps].sort((a, b) => score(b) - score(a));
  const hits = ranked.slice(0, k).filter((p) => score(p) > 0);
  return hits.length > 0 ? hits : ps.slice(0, k);
}
