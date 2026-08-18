"use client";

import { useState } from "react";
import { ArticleCard } from "@/components/ArticleCard";
import type { ArticlePresentation } from "@/lib/research/summarize";

export function ArticleGrid({
  query,
  articles,
  unavailable,
}: {
  query: string;
  articles: ArticlePresentation[];
  unavailable?: string[];
}) {
  const [tracking, setTracking] = useState(false);
  const [tracked, setTracked] = useState(false);

  async function handleTrack() {
    setTracking(true);
    try {
      const res = await fetch("/api/library/track", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      if (res.ok) setTracked(true);
    } finally {
      setTracking(false);
    }
  }

  if (articles.length === 0) {
    return <div className="article-grid-empty">No results found for &ldquo;{query}&rdquo;.</div>;
  }

  return (
    <div className="article-grid">
      <div className="article-grid-header">
        <button className="article-grid-track" onClick={handleTrack} disabled={tracked || tracking}>
          {tracked ? "Tracking topic ✓" : tracking ? "Tracking…" : "Track this topic (refresh every 2 days)"}
        </button>
      </div>
      {unavailable && unavailable.length > 0 && (
        <div className="article-grid-warning">
          {unavailable.join(", ")} temporarily unavailable — results may be incomplete.
        </div>
      )}
      {articles.map((a) => (
        <ArticleCard key={`${a.source}-${a.index}-${a.doi ?? a.title}`} article={a} />
      ))}
    </div>
  );
}
