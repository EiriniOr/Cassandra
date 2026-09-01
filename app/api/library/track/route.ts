import { NextRequest, NextResponse } from "next/server";
import { readUidCookie } from "@/lib/auth";
import { trackTopic, untrackTopic } from "@/lib/library";

export async function POST(req: NextRequest) {
  const uid = readUidCookie(req.cookies);
  if (!uid) return NextResponse.json({ error: "No library session" }, { status: 400 });

  const { query, label } = await req.json().catch(() => ({}) as { query?: unknown; label?: unknown });
  if (typeof query !== "string" || !query.trim()) {
    return NextResponse.json({ error: "query is required" }, { status: 400 });
  }

  const library = await trackTopic(uid, query, typeof label === "string" ? label : undefined);
  return NextResponse.json(library);
}

export async function DELETE(req: NextRequest) {
  const uid = readUidCookie(req.cookies);
  if (!uid) return NextResponse.json({ error: "No library session" }, { status: 400 });

  const { query } = await req.json().catch(() => ({}) as { query?: unknown });
  if (typeof query !== "string" || !query.trim()) {
    return NextResponse.json({ error: "query is required" }, { status: 400 });
  }

  const library = await untrackTopic(uid, query);
  return NextResponse.json(library);
}
