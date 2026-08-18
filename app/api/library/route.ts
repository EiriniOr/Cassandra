import { NextRequest, NextResponse } from "next/server";
import { readUidCookie } from "@/lib/auth";
import { getLibrary } from "@/lib/library";

export async function GET(req: NextRequest) {
  const uid = readUidCookie(req.cookies);
  if (!uid) return NextResponse.json({ error: "No library session" }, { status: 400 });
  return NextResponse.json(await getLibrary(uid));
}
