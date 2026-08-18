import { NextRequest, NextResponse } from "next/server";
import { readUidCookie } from "@/lib/auth";
import { articleDedupeKey, dismissNewFind } from "@/lib/library";

export async function DELETE(req: NextRequest) {
  const uid = readUidCookie(req.cookies);
  if (!uid) return NextResponse.json({ error: "No library session" }, { status: 400 });

  const article = (await req.json().catch(() => null)) as { doi?: string; title?: string } | null;
  if (!article?.title && !article?.doi) {
    return NextResponse.json({ error: "Invalid article" }, { status: 400 });
  }

  const library = await dismissNewFind(uid, articleDedupeKey({ doi: article.doi ?? null, title: article.title ?? "" }));
  return NextResponse.json(library);
}
