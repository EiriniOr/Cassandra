"use client";

import { useEffect, useState, type RefObject } from "react";

interface Line {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export function ConnectorLines({
  containerRef,
  hubRef,
  spokeRefs,
  active,
}: {
  containerRef: RefObject<HTMLElement | null>;
  hubRef: RefObject<HTMLElement | null>;
  spokeRefs: RefObject<(HTMLElement | null)[]>;
  active: boolean;
}) {
  const [lines, setLines] = useState<Line[]>([]);

  useEffect(() => {
    if (!active) {
      setLines([]);
      return;
    }

    function measure() {
      const container = containerRef.current;
      const hub = hubRef.current;
      if (!container || !hub) return;

      const containerRect = container.getBoundingClientRect();
      const hubRect = hub.getBoundingClientRect();
      const hubX = hubRect.left + hubRect.width / 2 - containerRect.left;
      const hubY = hubRect.bottom - containerRect.top;

      const next: Line[] = [];
      for (const spoke of spokeRefs.current ?? []) {
        if (!spoke) continue;
        const r = spoke.getBoundingClientRect();
        next.push({
          x1: hubX,
          y1: hubY,
          x2: r.left + r.width / 2 - containerRect.left,
          y2: r.top - containerRect.top,
        });
      }
      setLines(next);
    }

    measure();
    const observer = new ResizeObserver(measure);
    if (containerRef.current) observer.observe(containerRef.current);
    if (hubRef.current) observer.observe(hubRef.current);
    for (const spoke of spokeRefs.current ?? []) {
      if (spoke) observer.observe(spoke);
    }
    window.addEventListener("resize", measure);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", measure);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  if (lines.length === 0) return null;

  return (
    <svg className="connector-lines" aria-hidden="true">
      {lines.map((l, i) => {
        const midY = (l.y1 + l.y2) / 2;
        const d = `M ${l.x1} ${l.y1} C ${l.x1} ${midY}, ${l.x2} ${midY}, ${l.x2} ${l.y2}`;
        return <path key={i} d={d} />;
      })}
    </svg>
  );
}
