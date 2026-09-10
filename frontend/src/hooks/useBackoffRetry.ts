import { useConnectionStore } from "../state/connectionStore";
import { classifyError } from "../api/errorClassification";
import type { ApiClientError } from "../api/client";

const DELAYS_MS = [1000, 2000, 4000, 8000];

/**
 * Runs a background read (getStatus, listFlags) with quiet retries before
 * escalating to the shared connection banner. Most cold-start 502s resolve
 * within the first attempt or two and the banner never appears at all.
 * Returns a cancel function to call on unmount.
 */
export function runWithBackoff<T>(
  fn: () => Promise<T>,
  onSuccess: (result: T) => void,
  friendlyMessage = "Having trouble reaching the server.",
  friendlySubMessage?: string,
): () => void {
  let attempt = 0;
  let timeoutId: ReturnType<typeof setTimeout> | undefined;
  let cancelled = false;

  function attemptOnce() {
    fn()
      .then((result) => {
        if (cancelled) return;
        useConnectionStore.getState().setOk();
        onSuccess(result);
      })
      .catch((e) => {
        if (cancelled) return;
        const error = e as ApiClientError;
        const treatment = classifyError(error);

        if (treatment.kind !== "banner" || treatment.immediate || attempt >= DELAYS_MS.length) {
          useConnectionStore.getState().setDown(friendlyMessage, friendlySubMessage, () => {
            attempt = 0;
            attemptOnce();
          });
          return;
        }

        attempt += 1;
        useConnectionStore.getState().setRetrying(attempt, DELAYS_MS.length);
        timeoutId = setTimeout(attemptOnce, DELAYS_MS[attempt - 1]);
      });
  }

  attemptOnce();

  return () => {
    cancelled = true;
    if (timeoutId !== undefined) clearTimeout(timeoutId);
  };
}
