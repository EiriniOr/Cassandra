"use client";

import { useState } from "react";

export function BottomBar({ onSubmit, loading }: { onSubmit: (text: string) => void; loading: boolean }) {
  const [draft, setDraft] = useState("");

  return (
    <form
      className="bottom-bar"
      onSubmit={(e) => {
        e.preventDefault();
        if (!draft.trim()) return;
        onSubmit(draft);
        setDraft("");
      }}
    >
      <input
        className="bottom-bar__input"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        placeholder="What are you researching today?"
        disabled={loading}
      />
      <button className="bottom-bar__submit" type="submit" disabled={loading}>
        Ask
      </button>
    </form>
  );
}
