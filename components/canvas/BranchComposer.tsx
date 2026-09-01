"use client";

import { useState } from "react";

export function BranchComposer({ onSubmit }: { onSubmit: (text: string) => void }) {
  const [text, setText] = useState("");

  return (
    <form
      className="branch-composer"
      onSubmit={(e) => {
        e.preventDefault();
        if (!text.trim()) return;
        onSubmit(text);
        setText("");
      }}
    >
      <input
        className="branch-composer__input"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Ask about this…"
      />
      <button className="branch-composer__submit" type="submit" aria-label="Ask">
        →
      </button>
    </form>
  );
}
