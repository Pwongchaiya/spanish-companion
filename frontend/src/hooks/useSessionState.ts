import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type { ServerEvent } from "../api/types";
import { useSessionStore } from "../state/store";
import { useEventSource } from "./useEventSource";

export function useSessionState() {
  const status = useSessionStore((s) => s.status);
  const transcript = useSessionStore((s) => s.transcript);
  const turnState = useSessionStore((s) => s.turnState);
  const setStatus = useSessionStore((s) => s.setStatus);
  const applyEvent = useSessionStore((s) => s.applyEvent);
  const { data, connectionStatus } = useEventSource<ServerEvent>("/api/events");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient
      .getStatus()
      .then(setStatus)
      .catch((e) => setError((e as Error).message));
  }, [setStatus]);

  useEffect(() => {
    if (data) applyEvent(data);
  }, [data, applyEvent]);

  async function start() {
    setError(null);
    const previousStatus = status;
    setStatus({ running: true, ready: false, graceful: null });
    try {
      await apiClient.startSession();
    } catch (e) {
      setStatus(previousStatus);
      setError((e as Error).message);
    }
  }

  async function stop() {
    setError(null);
    try {
      await apiClient.stopSession();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return { status, transcript, turnState, connectionStatus, error, start, stop };
}
