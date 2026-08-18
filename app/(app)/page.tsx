"use client";

import Link from "next/link";
import { CopilotChat } from "@copilotkit/react-ui";
import { useCopilotAdditionalInstructions, useFrontendTool } from "@copilotkit/react-core";
import { SYSTEM_PROMPT } from "@/lib/prompt";
import { ArticleGrid } from "@/components/ArticleGrid";
import type { ArticlePresentation } from "@/lib/research/summarize";

interface SearchResponse {
  query: string;
  articles: ArticlePresentation[];
  unavailable: string[];
}

export default function Home() {
  useCopilotAdditionalInstructions({ instructions: SYSTEM_PROMPT });

  useFrontendTool({
    name: "search_literature",
    description:
      "Search scientific literature (OpenAlex + arXiv) for a research topic and present the results as interactive article cards. Always use this when the user wants sources, papers, or evidence — never invent citations yourself.",
    parameters: [
      {
        name: "query",
        type: "string",
        description: "The research topic or question to search for.",
        required: true,
      },
      {
        name: "maxResults",
        type: "number",
        description: "Max number of results (default 6, max 25).",
        required: false,
      },
    ],
    handler: async ({ query, maxResults }) => {
      const res = await fetch("/api/research/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, maxResults }),
      });
      if (!res.ok) {
        return { query, articles: [], unavailable: [] } satisfies SearchResponse;
      }
      return (await res.json()) as SearchResponse;
    },
    render: ({ status, args, result }) => {
      if (status !== "complete" || !result) {
        return <div className="article-grid-loading">Searching{args?.query ? ` "${args.query}"` : ""}…</div>;
      }
      return <ArticleGrid query={result.query} articles={result.articles} unavailable={result.unavailable} />;
    },
  });

  return (
    <main className="chat-shell">
      <header className="chat-header">
        <span className="brand">Cassandra</span>
        <span className="tagline">research assistant</span>
        <Link href="/library" className="chat-header__library">
          Your library
        </Link>
      </header>
      <CopilotChat
        className="chat-panel"
        labels={{
          title: "Cassandra",
          initial: "What are you researching today?",
        }}
      />
    </main>
  );
}
