"use client";

import { useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { AnswerNode } from "@/lib/canvas/types";
import { ArticleCard } from "@/components/ArticleCard";
import { ConnectorLines } from "@/components/canvas/ConnectorLines";
import { BranchComposer } from "@/components/canvas/BranchComposer";

function ancestryOf(node: AnswerNode, allNodes: Record<string, AnswerNode>): AnswerNode[] {
  const chain: AnswerNode[] = [];
  let current = node.parentId ? allNodes[node.parentId] : undefined;
  while (current) {
    chain.unshift(current);
    current = current.parentId ? allNodes[current.parentId] : undefined;
  }
  return chain;
}

export function AnswerHub({
  node,
  allNodes,
  onNavigate,
  onBranch,
}: {
  node: AnswerNode;
  allNodes: Record<string, AnswerNode>;
  onNavigate: (id: string) => void;
  onBranch: (parentId: string, text: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [tracking, setTracking] = useState(false);
  const [tracked, setTracked] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const hubRef = useRef<HTMLDivElement>(null);
  const spokeRefs = useRef<(HTMLElement | null)[]>([]);

  const pending = node.answerText === null;
  const hasFacts = node.facts.length > 0;
  const ancestry = ancestryOf(node, allNodes);

  async function handleTrack() {
    setTracking(true);
    try {
      const res = await fetch("/api/library/track", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: node.question }),
      });
      if (res.ok) setTracked(true);
    } catch {
      // library not configured yet (e.g. Upstash not connected) — fail quietly
    } finally {
      setTracking(false);
    }
  }

  return (
    <div className="hub-spoke-container" ref={containerRef}>
      <ConnectorLines containerRef={containerRef} hubRef={hubRef} spokeRefs={spokeRefs} active={expanded && hasFacts} />

      <div className="answer-hub" ref={hubRef}>
        {ancestry.length > 0 && (
          <div className="answer-hub__breadcrumb">
            {ancestry.map((a) => (
              <span key={a.id}>
                <button onClick={() => onNavigate(a.id)}>{a.question}</button>
                <span className="answer-hub__breadcrumb-sep">›</span>
              </span>
            ))}
          </div>
        )}

        <div className="answer-hub__question">{node.question}</div>
        {pending ? (
          <div className="answer-hub__pending">Thinking…</div>
        ) : (
          <div className="answer-hub__text">{node.answerText}</div>
        )}
        {!pending && (
          <div className="answer-hub__row">
            <button className="answer-hub__toggle" onClick={() => setExpanded((e) => !e)}>
              {expanded
                ? "Collapse"
                : hasFacts
                  ? `Show ${node.facts.length} source${node.facts.length > 1 ? "s" : ""}`
                  : "Discuss further"}
            </button>
            {hasFacts && (
              <button className="answer-hub__track" onClick={handleTrack} disabled={tracked || tracking}>
                {tracked ? "Tracking topic ✓" : tracking ? "Tracking…" : "Track this topic"}
              </button>
            )}
          </div>
        )}

        {expanded && (
          <div className="answer-hub__branch">
            <BranchComposer onSubmit={(text) => onBranch(node.id, text)} />
          </div>
        )}
      </div>

      <AnimatePresence>
        {expanded && hasFacts && (
          <motion.div className="fact-spokes" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            {node.facts.map((f, i) => (
              <motion.div
                key={`${f.source}-${f.index}-${f.doi ?? f.title}`}
                className="fact-spoke"
                ref={(el) => {
                  spokeRefs.current[i] = el;
                }}
                initial={{ opacity: 0, y: -12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
              >
                <ArticleCard article={f} />
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {node.children.length > 0 && (
        <div className="answer-hub__children">
          {node.children.map((childId) => {
            const child = allNodes[childId];
            if (!child) return null;
            return (
              <button key={childId} className="answer-hub__child-pill" onClick={() => onNavigate(childId)}>
                {child.question}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
