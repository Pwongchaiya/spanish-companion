import { useEffect } from "react";
import { apiClient } from "../api/client";
import type { ServerEvent } from "../api/types";
import { useSessionStore } from "../state/store";
import { useEventSource } from "./useEventSource";

export function useSessionState() {
  const status = useSessionStore((s) => s.status);
  const transcript = useSessionStore((s) => s.transcript);
  const setStatus = useSessionStore((s) => s.setStatus);
  const applyEvent = useSessionStore((s) => s.applyEvent);
  const { data, connectionStatus } = useEventSource<ServerEvent>("/api/events");

  useEffect(() => {
    apiClient.getStatus().then(setStatus);
  }, [setStatus]);

  useEffect(() => {
    if (data) applyEvent(data);
  }, [data, applyEvent]);

  async function start() {
    setStatus({ running: true, ready: false, graceful: null });
    await apiClient.startSession();
  }

  async function stop() {
    await apiClient.stopSession();
  }

  return { status, transcript, connectionStatus, start, stop };
}
