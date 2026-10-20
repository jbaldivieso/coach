import type { RouteLocationRaw } from "vue-router";

/** ?next= when it's a path on this site; "//host" and "/\host" would leave it. */
export function safeNextPath(next: unknown): string | null {
  if (typeof next !== "string" || !next.startsWith("/")) return null;
  if (next.startsWith("//") || next.startsWith("/\\")) return null;
  return next;
}

/**
 * Where to go after signing in. Django serves the OAuth consent page, not the
 * SPA, so that one gets a full page load and this returns null.
 */
export function followNext(next: unknown): RouteLocationRaw | null {
  const path = safeNextPath(next);
  if (path?.startsWith("/oauth/")) {
    window.location.assign(path);
    return null;
  }
  return path ?? { name: "home" };
}
