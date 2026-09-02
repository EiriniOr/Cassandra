"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { ArticlePresentation } from "@/lib/research/summarize";

type Zoom = "sentence" | "paragraph" | "pdf";

function nextZoom(zoom: Zoom, hasPdf: boolean): Zoom {
  if (zoom === "sentence") return "paragraph";
  if (zoom === "paragraph") return hasPdf ? "pdf" : "sentence";
  return "sentence";
}

function zoomTitle(zoom: Zoom, hasPdf: boolean): string {
  if (zoom === "sentence") return "Expand to paragraph";
  if (zoom === "paragraph") return hasPdf ? "Expand to full article (PDF)" : "Not open access — collapse";
  return "Collapse";
}

const CARD_SPRING = { type: "spring" as const, stiffness: 300, damping: 30 };
const FADE = { duration: 0.14, ease: "easeOut" as const };

export function ArticleCard({ article }: { article: ArticlePresentation }) {
  const [zoom, setZoom] = useState<Zoom>("sentence");
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const hasPdf = Boolean(article.pdfUrl);

  async function handleSave() {
    setSaving(true);
    try {
      const res = await fetch("/api/library/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(article),
      });
      if (res.ok) setSaved(true);
    } catch {
      // library not configured yet (e.g. Upstash not connected) — fail quietly
    } finally {
      setSaving(false);
    }
  }

  return (
    <motion.div layout className={`article-card article-card--${zoom}`} transition={CARD_SPRING}>
      <motion.button
        className="article-card__zoom"
        onClick={() => setZoom((z) => nextZoom(z, hasPdf))}
        title={zoomTitle(zoom, hasPdf)}
        aria-label={zoomTitle(zoom, hasPdf)}
        whileHover={{ scale: 1.12 }}
        whileTap={{ scale: 0.92 }}
      >
        {zoom === "pdf" ? "−" : "+"}
      </motion.button>

      <div className="article-card__body">
        <AnimatePresence mode="popLayout" initial={false}>
          {zoom === "sentence" && (
            <motion.p
              key="sentence"
              className="article-card__sentence"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={FADE}
            >
              {article.sentence}
            </motion.p>
          )}

          {zoom === "paragraph" && (
            <motion.p
              key="paragraph"
              className="article-card__paragraph"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={FADE}
            >
              {article.paragraph}
            </motion.p>
          )}

          {zoom === "pdf" && article.pdfUrl && (
            <motion.div
              key="pdf"
              className="article-card__pdf"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={FADE}
            >
              <iframe src={article.pdfUrl} title={article.title} />
            </motion.div>
          )}
        </AnimatePresence>

        <div className="article-card__source">
          {article.url ? (
            <a className="article-card__source-title" href={article.url} target="_blank" rel="noreferrer">
              {article.title}
            </a>
          ) : (
            <span className="article-card__source-title">{article.title}</span>
          )}
          <div className="article-card__source-meta">
            <span>{article.authors.slice(0, 2).join(", ") || "Unknown authors"}</span>
            <span aria-hidden="true">·</span>
            <span>{article.year ?? "n.d."}</span>
            <span aria-hidden="true">·</span>
            <span>{article.source === "arxiv" ? "arXiv" : "OpenAlex"}</span>
            <button className="article-card__save" onClick={handleSave} disabled={saved || saving}>
              {saved ? "Saved" : saving ? "Saving…" : "Save"}
            </button>
          </div>
          {zoom !== "sentence" && !hasPdf && (
            <span className="article-card__not-oa">Not open access — no full text available</span>
          )}
        </div>
      </div>
    </motion.div>
  );
}
