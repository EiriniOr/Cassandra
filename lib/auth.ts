// Password-gate helpers. Uses Web Crypto (SubtleCrypto) only, so this module
// works unmodified in both the Edge middleware runtime and Node API routes.

const AUTH_COOKIE = "cassandra_auth";
const UID_COOKIE = "cassandra_uid";
const SESSION_VALUE = "ok";

function toBase64Url(bytes: ArrayBuffer): string {
  const b64 = btoa(String.fromCharCode(...new Uint8Array(bytes)));
  return b64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

async function hmacKey(secret: string): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
}

async function sign(value: string, secret: string): Promise<string> {
  const key = await hmacKey(secret);
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(value));
  return `${value}.${toBase64Url(sig)}`;
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export async function createSessionCookieValue(secret: string): Promise<string> {
  return sign(SESSION_VALUE, secret);
}

export async function isValidSessionCookie(
  cookieValue: string | undefined,
  secret: string,
): Promise<boolean> {
  if (!cookieValue) return false;
  const dot = cookieValue.lastIndexOf(".");
  if (dot === -1) return false;
  const value = cookieValue.slice(0, dot);
  if (value !== SESSION_VALUE) return false;
  const expected = await sign(SESSION_VALUE, secret);
  return timingSafeEqual(cookieValue, expected);
}

export function generateUid(): string {
  return crypto.randomUUID();
}

export const AUTH_COOKIE_NAME = AUTH_COOKIE;
export const UID_COOKIE_NAME = UID_COOKIE;

/** Read the opaque library-scoping uid cookie from a NextRequest's cookie jar. */
export function readUidCookie(cookies: { get(name: string): { value: string } | undefined }): string | null {
  return cookies.get(UID_COOKIE_NAME)?.value ?? null;
}
