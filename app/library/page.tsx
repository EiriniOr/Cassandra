"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import "../globals.css";
import type { Library, SavedArticle } from "@/lib/library";

export default function LibraryPage() {
  const [library, setLibrary] = useState<Library | null>(null);

  async function load() {
    try {
      const res = await fetch("/api/library");
      if (res.ok) setLibrary(await res.json());
    } catch {
      // library not configured yet (e.g. Upstash not connected)
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function untrack(query: string) {
    try {
      await fetch("/api/library/track", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
    } catch {
      // ignore
    }
    load();
  }

  async function saveFind(article: SavedArticle) {
    try {
      await fetch("/api/library/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(article),
      });
    } catch {
      // ignore
    }
    load();
  }

  async function dismissFind(article: SavedArticle) {
    try {
      await fetch("/api/library/newfinds", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doi: article.doi, title: article.title }),
      });
    } catch {
      // ignore
    }
    load();
  }

  return (
    <div className="library-shell">
      <Link href="/" className="library-back">
        ← Back to chat
      </Link>
      <h1>Your library</h1>
      {library?.lastRefresh && (
        <p className="library-empty">Last refreshed {new Date(library.lastRefresh).toLocaleString()}</p>
      )}

      {library && library.newFinds.length > 0 && (
        <>
          <h2>New since last refresh</h2>
          {library.newFinds.map((a) => (
            <div className="library-article-row" key={`${a.doi ?? a.title}`}>
              <div>
                <div className="library-article-row__title">{a.title}</div>
                <div className="library-article-row__meta">
                  {a.authors.slice(0, 3).join(", ") || "Unknown authors"} · {a.year ?? "n.d."}
                </div>
              </div>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button className="library-untrack" onClick={() => saveFind(a)}>
                  Save
                </button>
                <button className="library-untrack" onClick={() => dismissFind(a)}>
                  Dismiss
                </button>
              </div>
            </div>
          ))}
        </>
      )}

      <h2>Tracked topics</h2>
      {!library ? (
        <p className="library-empty">Loading…</p>
      ) : library.trackedTopics.length === 0 ? (
        <p className="library-empty">No tracked topics yet — track one from a search result.</p>
      ) : (
        library.trackedTopics.map((t) => (
          <div className="library-topic-row" key={t.query}>
            <span className="library-topic-row__label">{t.label}</span>
            <button className="library-untrack" onClick={() => untrack(t.query)}>
              Untrack
            </button>
          </div>
        ))
      )}

      <h2>Saved articles</h2>
      {!library ? null : library.savedArticles.length === 0 ? (
        <p className="library-empty">No saved articles yet — save one from a search result.</p>
      ) : (
        library.savedArticles.map((a) => (
          <div className="library-article-row" key={`${a.doi ?? a.title}`}>
            <div>
              <div className="library-article-row__title">{a.title}</div>
              <div className="library-article-row__meta">
                {a.authors.slice(0, 3).join(", ") || "Unknown authors"} · {a.year ?? "n.d."}
              </div>
            </div>
            {a.url && (
              <a href={a.url} target="_blank" rel="noreferrer">
                Open ↗
              </a>
            )}
          </div>
        ))
      )}
    </div>
  );
}
