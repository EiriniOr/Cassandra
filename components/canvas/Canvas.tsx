"use client";

import { AnimatePresence, motion } from "framer-motion";
import type { AnswerNode } from "@/lib/canvas/types";
import { AnswerHub } from "@/components/canvas/AnswerHub";

export function Canvas({
  node,
  allNodes,
  onNavigate,
  onBranch,
}: {
  node: AnswerNode | null;
  allNodes: Record<string, AnswerNode>;
  onNavigate: (id: string) => void;
  onBranch: (parentId: string, text: string) => void;
}) {
  if (!node) {
    return (
      <div className="canvas-empty">
        <p>What are you researching today?</p>
      </div>
    );
  }
  return (
    <div className="canvas">
      <AnimatePresence mode="wait">
        <motion.div
          key={node.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
          style={{ width: "100%", display: "flex", justifyContent: "center" }}
        >
          <AnswerHub node={node} allNodes={allNodes} onNavigate={onNavigate} onBranch={onBranch} />
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
