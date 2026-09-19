import { useState, useCallback, useRef, useEffect } from "react";

export type RecorderStatus = "idle" | "recording" | "done" | "error";

export const MAX_RECORD_MS = 15_000;

const MIME_CANDIDATES = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];

function pickMimeType(): string | undefined {
  return MIME_CANDIDATES.find((m) => MediaRecorder.isTypeSupported(m));
}

// Own getUserMedia (not useMicPermission, which stops tracks immediately).
export function useRecorder() {
  const [status, setStatus] = useState<RecorderStatus>("idle");
  const [blob, setBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const release = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }, []);

  const stop = useCallback(() => {
    const rec = recorderRef.current;
    if (rec && rec.state !== "inactive") rec.stop(); // onstop releases tracks
    else release();
  }, [release]);

  const start = useCallback(async () => {
    setBlob(null);
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mimeType = pickMimeType();
      const rec = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      const chunks: Blob[] = [];
      rec.ondataavailable = (e) => chunks.push(e.data);
      rec.onstop = () => {
        release();
        setBlob(new Blob(chunks, { type: rec.mimeType || mimeType || "audio/webm" }));
        setStatus("done");
      };
      recorderRef.current = rec;
      rec.start();
      setStatus("recording");
      timerRef.current = setTimeout(stop, MAX_RECORD_MS);
    } catch (err) {
      release();
      const isDenied =
        err instanceof DOMException && (err.name === "NotAllowedError" || err.name === "PermissionDeniedError");
      setStatus("error");
      setError(isDenied ? "Microphone permission denied." : err instanceof Error ? err.message : String(err));
    }
  }, [release, stop]);

  useEffect(
    () => () => {
      const rec = recorderRef.current;
      if (rec) rec.onstop = null; // unmounted: don't set state
      if (rec && rec.state !== "inactive") rec.stop();
      release();
    },
    [release],
  );

  return { status, blob, error, start, stop };
}
