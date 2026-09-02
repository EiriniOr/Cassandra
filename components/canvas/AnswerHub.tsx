"use client";

import { useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { AnswerNode } from "@/lib/canvas/types";
import type { ArticlePresentation } from "@/lib/research/summarize";
import { ArticleCard } from "@/components/ArticleCard";
import { ConnectorLines } from "@/components/canvas/ConnectorLines";
import { BranchComposer } from "@/components/canvas/BranchComposer";

const SPRING = { type: "spring" as const, stiffness: 300, damping: 28 };
/** Sources up to this count spread sideways in one row below the hub; beyond it, split above/below to wrap around the hub instead of stacking further down. */
const SINGLE_ROW_CAPACITY = 4;

function ancestryOf(node: AnswerNode, allNodes: Record<string, AnswerNode>): AnswerNode[] {
  const chain: AnswerNode[] = [];
  let current = node.parentId ? allNodes[node.parentId] : undefined;
  while (current) {
    chain.unshift(current);
    current = current.parentId ? allNodes[current.parentId] : undefined;
  }
  return chain;
}

function keyFor(f: ArticlePresentation): string {
  return `${f.source}-${f.index}-${f.doi ?? f.title}`;
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
  const [trackState, setTrackState] = useState<"idle" | "tracking" | "tracked" | "error">("idle");
  const containerRef = useRef<HTMLDivElement>(null);
  const hubRef = useRef<HTMLDivElement>(null);
  const belowRefs = useRef<(HTMLElement | null)[]>([]);
  const aboveRefs = useRef<(HTMLElement | null)[]>([]);

  const pending = node.answerText === null;
  const hasFacts = node.facts.length > 0;
  const ancestry = ancestryOf(node, allNodes);

  const overflow = node.facts.length > SINGLE_ROW_CAPACITY;
  const belowFacts = overflow ? node.facts.slice(0, Math.ceil(node.facts.length / 2)) : node.facts;
  const aboveFacts = overflow ? node.facts.slice(Math.ceil(node.facts.length / 2)) : [];

  async function handleTrack() {
    setTrackState("tracking");
    try {
      const res = await fetch("/api/library/track", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: node.question }),
      });
      setTrackState(res.ok ? "tracked" : "error");
    } catch {
      setTrackState("error");
    }
  }

  const trackLabel = {
    idle: "Track this topic",
    tracking: "Tracking…",
    tracked: "Tracking topic ✓",
    error: "Couldn't track — retry",
  }[trackState];

  return (
    <div className="hub-spoke-container" ref={containerRef}>
      <ConnectorLines
        containerRef={containerRef}
        hubRef={hubRef}
        belowRefs={belowRefs}
        aboveRefs={aboveRefs}
        active={expanded && hasFacts}
      />

      <AnimatePresence>
        {expanded && aboveFacts.length > 0 && (
          <motion.div
            className="fact-spokes fact-spokes--above"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            {aboveFacts.map((f, i) => (
              <motion.div
                key={keyFor(f)}
                className="fact-spoke"
                ref={(el) => {
                  aboveRefs.current[i] = el;
                }}
                initial={{ opacity: 0, y: 16, scale: 0.94 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.94 }}
                transition={{ ...SPRING, delay: i * 0.07 }}
              >
                <ArticleCard article={f} />
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div layout className="answer-hub" ref={hubRef} transition={SPRING}>
        {ancestry.length > 0 && (
          <div className="answer-hub__breadcrumb">
            {ancestry.map((a) => (
              <span key={a.id}>
                <motion.button whileHover={{ x: -2 }} onClick={() => onNavigate(a.id)}>
                  {a.question}
                </motion.button>
                <span className="answer-hub__breadcrumb-sep">›</span>
              </span>
            ))}
          </div>
        )}

        <div className="answer-hub__question">{node.question}</div>
        <AnimatePresence mode="wait">
          {pending ? (
            <motion.div
              key="pending"
              className="answer-hub__pending"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              Thinking…
            </motion.div>
          ) : (
            <motion.div
              key="text"
              className="answer-hub__text"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={SPRING}
            >
              {node.answerText}
            </motion.div>
          )}
        </AnimatePresence>

        {!pending && (
          <motion.div layout className="answer-hub__row">
            <motion.button
              className="answer-hub__toggle"
              onClick={() => setExpanded((e) => !e)}
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.97 }}
            >
              {expanded
                ? "Collapse"
                : hasFacts
                  ? `Show ${node.facts.length} source${node.facts.length > 1 ? "s" : ""}`
                  : "Discuss further"}
            </motion.button>
            {hasFacts && (
              <motion.button
                className="answer-hub__track"
                onClick={handleTrack}
                disabled={trackState === "tracking" || trackState === "tracked"}
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.97 }}
              >
                {trackLabel}
              </motion.button>
            )}
          </motion.div>
        )}

        <AnimatePresence>
          {expanded && (
            <motion.div
              className="answer-hub__branch"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={SPRING}
            >
              <BranchComposer onSubmit={(text) => onBranch(node.id, text)} />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      <AnimatePresence>
        {expanded && belowFacts.length > 0 && (
          <motion.div className="fact-spokes" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            {belowFacts.map((f, i) => (
              <motion.div
                key={keyFor(f)}
                className="fact-spoke"
                ref={(el) => {
                  belowRefs.current[i] = el;
                }}
                initial={{ opacity: 0, y: -16, scale: 0.94 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.94 }}
                transition={{ ...SPRING, delay: i * 0.07 }}
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
              <motion.button
                key={childId}
                className="answer-hub__child-pill"
                onClick={() => onNavigate(childId)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.96 }}
              >
                {child.question}
              </motion.button>
            );
          })}
        </div>
      )}
    </div>
  );
}
