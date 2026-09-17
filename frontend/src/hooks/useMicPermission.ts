import { useState, useCallback } from "react";

export type MicPermissionStatus = "idle" | "granted" | "denied" | "error";

// ponytail: standalone WebRTC spike step (browser mic permission only) --
// not wired to any backend signaling yet. See
// decisions/voice-conversation-browser-webrtc-transport.md.
export function useMicPermission() {
  const [status, setStatus] = useState<MicPermissionStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  const requestMic = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
      setStatus("granted");
      setError(null);
    } catch (err) {
      const isDenied =
        err instanceof DOMException &&
        (err.name === "NotAllowedError" || err.name === "PermissionDeniedError");
      setStatus(isDenied ? "denied" : "error");
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  return { status, error, requestMic };
}
