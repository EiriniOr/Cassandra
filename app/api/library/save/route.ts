import { NextRequest, NextResponse } from "next/server";
import { readUidCookie } from "@/lib/auth";
import { saveArticle } from "@/lib/library";
import type { ArticlePresentation } from "@/lib/research/summarize";

export async function POST(req: NextRequest) {
  const uid = readUidCookie(req.cookies);
  if (!uid) return NextResponse.json({ error: "No library session" }, { status: 400 });

  const article = (await req.json().catch(() => null)) as ArticlePresentation | null;
  if (!article || typeof article.title !== "string") {
    return NextResponse.json({ error: "Invalid article" }, { status: 400 });
  }

  const library = await saveArticle(uid, article);
  return NextResponse.json(library);
}
