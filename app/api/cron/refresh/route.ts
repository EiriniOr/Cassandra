import { NextRequest, NextResponse } from "next/server";
import { allLibraryUids, refreshLibrary } from "@/lib/library";

// Vercel Cron sends `Authorization: Bearer $CRON_SECRET` automatically for its
// own invocations when CRON_SECRET is set on the project — this both keeps
// outsiders from spamming the route and doubles as the "stay warm" ping.
export async function GET(req: NextRequest) {
  const expected = process.env.CRON_SECRET;
  if (!expected || req.headers.get("authorization") !== `Bearer ${expected}`) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const uids = await allLibraryUids();
  const results = await Promise.all(
    uids.map(async (uid) => {
      try {
        return await refreshLibrary(uid);
      } catch (err) {
        return { uid, error: String(err) };
      }
    }),
  );

  return NextResponse.json({ refreshed: results.length, results });
}
