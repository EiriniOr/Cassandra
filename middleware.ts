import { NextRequest, NextResponse } from "next/server";
import {
  AUTH_COOKIE_NAME,
  UID_COOKIE_NAME,
  generateUid,
  isValidSessionCookie,
} from "@/lib/auth";

// /api/cron is not cookie-gated — it has its own CRON_SECRET bearer-token
// check (see app/api/cron/refresh/route.ts), since Vercel Cron invocations
// carry no browser session cookie.
const PUBLIC_PATHS = ["/login", "/api/login", "/api/cron"];

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  if (PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(p + "/"))) {
    return NextResponse.next();
  }

  const secret = process.env.AUTH_SECRET;
  if (!secret) {
    return new NextResponse("Server misconfigured: AUTH_SECRET not set", { status: 500 });
  }

  const authed = await isValidSessionCookie(
    req.cookies.get(AUTH_COOKIE_NAME)?.value,
    secret,
  );

  if (!authed) {
    const loginUrl = new URL("/login", req.url);
    return NextResponse.redirect(loginUrl);
  }

  const res = NextResponse.next();
  if (!req.cookies.get(UID_COOKIE_NAME)?.value) {
    res.cookies.set(UID_COOKIE_NAME, generateUid(), {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      maxAge: 60 * 60 * 24 * 365,
      path: "/",
    });
  }
  return res;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
