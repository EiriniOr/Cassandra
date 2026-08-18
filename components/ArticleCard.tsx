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
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className={`article-card article-card--${zoom}`}>
      <button
        className="article-card__zoom"
        onClick={() => setZoom((z) => nextZoom(z, hasPdf))}
        title={zoomTitle(zoom, hasPdf)}
        aria-label={zoomTitle(zoom, hasPdf)}
      >
        {zoom === "pdf" ? "−" : "+"}
      </button>

      <div className="article-card__body">
        <div className="article-card__meta">
          <span className="article-card__source">{article.source === "arxiv" ? "arXiv" : "OpenAlex"}</span>
          <span className="article-card__year">{article.year ?? "n.d."}</span>
        </div>
        <div className="article-card__title">{article.title}</div>
        <div className="article-card__authors">{article.authors.slice(0, 3).join(", ") || "Unknown authors"}</div>

        <AnimatePresence mode="wait" initial={false}>
          {zoom === "sentence" && (
            <motion.p
              key="sentence"
              className="article-card__sentence"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {article.sentence}
            </motion.p>
          )}

          {zoom === "paragraph" && (
            <motion.div
              key="paragraph"
              className="article-card__paragraph"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
            >
              <p>{article.paragraph}</p>
              <div className="article-card__actions">
                {article.url && (
                  <a href={article.url} target="_blank" rel="noreferrer">
                    Source ↗
                  </a>
                )}
                <button className="article-card__save" onClick={handleSave} disabled={saved || saving}>
                  {saved ? "Saved" : saving ? "Saving…" : "Save"}
                </button>
                {!hasPdf && <span className="article-card__not-oa">Not open access — no full text available</span>}
              </div>
            </motion.div>
          )}

          {zoom === "pdf" && article.pdfUrl && (
            <motion.div
              key="pdf"
              className="article-card__pdf"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <iframe src={article.pdfUrl} title={article.title} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
