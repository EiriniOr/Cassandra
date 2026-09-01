"use client";

import { useState } from "react";
import Link from "next/link";
import type Anthropic from "@anthropic-ai/sdk";
import type { AnswerNode } from "@/lib/canvas/types";
import { Canvas } from "@/components/canvas/Canvas";
import { BottomBar } from "@/components/BottomBar";
import { HistoryDrawer } from "@/components/HistoryDrawer";

interface AskResponse {
  answerText: string;
  facts: AnswerNode["facts"];
  unavailable: string[];
  history: Anthropic.MessageParam[];
  error?: string;
}

export default function Home() {
  const [nodes, setNodes] = useState<Record<string, AnswerNode>>({});
  const [order, setOrder] = useState<string[]>([]);
  const [history, setHistory] = useState<Anthropic.MessageParam[]>([]);
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submitQuestion(question: string, parentId: string | null) {
    const id = crypto.randomUUID();
    const node: AnswerNode = {
      id,
      parentId,
      question,
      answerText: null,
      facts: [],
      children: [],
      createdAt: order.length,
    };

    setNodes((prev) => {
      const next = { ...prev, [id]: node };
      if (parentId && next[parentId]) {
        next[parentId] = { ...next[parentId], children: [...next[parentId].children, id] };
      }
      return next;
    });
    setOrder((prev) => [...prev, id]);
    setFocusedNodeId(id);
    setLoading(true);

    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, history }),
      });
      const data = (await res.json()) as AskResponse;
      if (!res.ok) {
        setNodes((prev) => ({
          ...prev,
          [id]: { ...prev[id], answerText: `Error: ${data.error ?? "request failed"}` },
        }));
        return;
      }
      setHistory(data.history);
      setNodes((prev) => ({
        ...prev,
        [id]: { ...prev[id], answerText: data.answerText, facts: data.facts },
      }));
    } catch (err) {
      setNodes((prev) => ({
        ...prev,
        [id]: { ...prev[id], answerText: `Error: ${err instanceof Error ? err.message : "request failed"}` },
      }));
    } finally {
      setLoading(false);
    }
  }

  const focusedNode = focusedNodeId ? (nodes[focusedNodeId] ?? null) : null;

  return (
    <main className="chat-shell">
      <header className="chat-header">
        <span className="brand">Cassandra</span>
        <span className="tagline">research assistant</span>
        <Link href="/library" className="chat-header__library">
          Your library
        </Link>
      </header>

      <Canvas
        node={focusedNode}
        allNodes={nodes}
        onNavigate={setFocusedNodeId}
        onBranch={(parentId, text) => submitQuestion(text, parentId)}
      />

      <HistoryDrawer order={order} nodes={nodes} onSelect={setFocusedNodeId}>
        <BottomBar onSubmit={(text) => submitQuestion(text, null)} loading={loading} />
      </HistoryDrawer>
    </main>
  );
}
