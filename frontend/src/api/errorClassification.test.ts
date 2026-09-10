import { describe, it, expect } from "vitest";
import { classifyError } from "./errorClassification";
import type { ApiClientError } from "./client";

function err(message: string, status?: number): ApiClientError {
  const e = new Error(message) as ApiClientError;
  e.status = status;
  return e;
}

describe("classifyError", () => {
  it("500 -> banner, immediate", () => {
    expect(classifyError(err("Request failed: 500", 500))).toEqual({ kind: "banner", immediate: true });
  });

  it.each([502, 503, 504])("%i -> banner, after backoff", (status) => {
    expect(classifyError(err(`Request failed: ${status}`, status))).toEqual({ kind: "banner", immediate: false });
  });

  it("no status (network/CORS failure) -> banner, after backoff", () => {
    expect(classifyError(err("Failed to fetch", undefined))).toEqual({ kind: "banner", immediate: false });
  });

  it("4xx with a real server message -> field, verbatim", () => {
    const e = err("Write the whole sentence, not just the corrected word.", 422);
    expect(classifyError(e)).toEqual({ kind: "field", message: e.message });
  });

  it("4xx with the client.ts fallback string (no body) -> toast", () => {
    const e = err("Request failed: 404", 404);
    expect(classifyError(e)).toEqual({ kind: "toast", message: e.message });
  });
});
