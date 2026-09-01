"use client";

import { useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { AnswerNode } from "@/lib/canvas/types";

export function HistoryDrawer({
  order,
  nodes,
  onSelect,
  children,
}: {
  order: string[];
  nodes: Record<string, AnswerNode>;
  onSelect: (id: string) => void;
  children: ReactNode;
}) {
  const [hover, setHover] = useState(false);
  const turns = order.map((id) => nodes[id]).filter(Boolean);

  return (
    <div className="history-wrap" onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}>
      <AnimatePresence>
        {hover && turns.length > 0 && (
          <motion.div
            className="history-panel"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.18 }}
          >
            <div className="history-panel__list">
              {turns.map((n) => (
                <button key={n.id} className="history-panel__row" onClick={() => onSelect(n.id)}>
                  <span className="history-panel__q">{n.question}</span>
                  <span className="history-panel__a">
                    {n.answerText ? n.answerText.slice(0, 100) : "…"}
                  </span>
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {!hover && turns.length > 0 && <div className="history-handle" aria-hidden="true" />}

      {children}
    </div>
  );
}
