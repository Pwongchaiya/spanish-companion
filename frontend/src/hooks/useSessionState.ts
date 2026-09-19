import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type { ApiClientError } from "../api/client";
import type { ServerEvent, SessionScenario } from "../api/types";
import { useSessionStore } from "../state/store";
import { useEventSource } from "./useEventSource";
import { useConnectionStore } from "../state/connectionStore";
import { useToastStore } from "../state/toastStore";
import { classifyError } from "../api/errorClassification";
import { runWithBackoff } from "./useBackoffRetry";

export function useSessionState() {
  const status = useSessionStore((s) => s.status);
  const transcript = useSessionStore((s) => s.transcript);
  const turnState = useSessionStore((s) => s.turnState);
  const setStatus = useSessionStore((s) => s.setStatus);
  const applyEvent = useSessionStore((s) => s.applyEvent);
  const { data, connectionStatus } = useEventSource<ServerEvent>("/api/events");

  // Suggested scenario for the next session (LearnerProfile Phase 3) --
  // fetched once while idle, not re-fetched while a session is running.
  // Fetch failure is silent: the scenario picker is optional, never
  // load-bearing for starting a conversation.
  const [scenario, setScenario] = useState<SessionScenario | null>(null);
  useEffect(() => {
    if (status.running) return;
    let cancelled = false;
    apiClient
      .getSessionScenario()
      .then((s) => {
        if (!cancelled) setScenario(s);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [status.running]);

  useEffect(() => {
    return runWithBackoff(() => apiClient.getStatus(), setStatus);
  }, [setStatus]);

  useEffect(() => {
    if (data) applyEvent(data);
  }, [data, applyEvent]);

  useEffect(() => {
    if (connectionStatus === "error") {
      useConnectionStore.getState().noteTransientIssue();
    } else if (connectionStatus === "open") {
      const { phase, maxAttempts } = useConnectionStore.getState();
      if (phase === "retrying" && maxAttempts === 0) {
        useConnectionStore.getState().setOk();
      }
    }
  }, [connectionStatus]);

  function handleActionError(e: unknown, retryAction: () => void, friendlyMessage: string, friendlySubMessage: string) {
    const error = e as ApiClientError;
    const treatment = classifyError(error);
    if (treatment.kind === "banner") {
      useConnectionStore.getState().setDown("Having trouble reaching the server.", undefined, retryAction);
    } else {
      useToastStore.getState().addToast(friendlyMessage, { subMessage: friendlySubMessage, retry: retryAction });
    }
  }

  async function start(
    scenarioText?: string,
    sessionLengthHint?: string,
    pressureLevel?: string,
    variant?: string,
    scenarioSlug?: string,
  ) {
    const previousStatus = status;
    setStatus({ running: true, ready: false, graceful: null });
    try {
      await apiClient.startSession(scenarioText, sessionLengthHint, pressureLevel, variant, scenarioSlug);
    } catch (e) {
      setStatus(previousStatus);
      handleActionError(
        e,
        () => start(scenarioText, sessionLengthHint, pressureLevel, variant, scenarioSlug),
        "Couldn't start the conversation.",
        "Try again when you're ready.",
      );
    }
  }

  async function stop() {
    try {
      await apiClient.stopSession();
    } catch (e) {
      handleActionError(e, stop, "Couldn't stop the conversation.", "You can try again, or just close the tab.");
    }
  }

  return { status, transcript, turnState, connectionStatus, scenario, start, stop };
}
