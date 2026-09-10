import type { ApiClientError } from "./client";

export type ErrorTreatment =
  | { kind: "banner"; immediate: boolean }
  | { kind: "field"; message: string }
  | { kind: "toast"; message: string };

/**
 * Where a caught request error should surface. Mirrors the Aliento
 * error-handling mockup's rule table:
 *   502/503/504/network -> banner, after backoff
 *   500                 -> banner, immediately (a crash isn't a cold start)
 *   4xx with a real body -> shown at the field, verbatim
 *   4xx with no body     -> deduped toast
 * client.ts's `Request failed: ${status}` fallback is how we tell "no body"
 * apart from "the server told us something" -- that fallback stays as-is
 * for the console; this is the one place it gets read.
 */
export function classifyError(error: ApiClientError): ErrorTreatment {
  const status = error.status;

  if (status === 500) return { kind: "banner", immediate: true };
  if (status === undefined || status === 502 || status === 503 || status === 504) {
    return { kind: "banner", immediate: false };
  }

  const isFallback = error.message === `Request failed: ${status}`;
  if (!isFallback) return { kind: "field", message: error.message };
  return { kind: "toast", message: error.message };
}
