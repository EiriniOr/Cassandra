import type { ArticlePresentation } from "@/lib/research/summarize";

export interface AnswerNode {
  id: string;
  parentId: string | null;
  question: string;
  answerText: string | null;
  facts: ArticlePresentation[];
  children: string[];
  /** Insertion order, not a wall-clock time. */
  createdAt: number;
}
