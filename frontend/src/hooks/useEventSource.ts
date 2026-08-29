import { useEffect, useState } from "react";

export type ConnectionStatus = "connecting" | "open" | "error";

export function useEventSource<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("connecting");
  const [error, setError] = useState<Event | null>(null);

  useEffect(() => {
    const source = new EventSource(url);

    source.onopen = () => setConnectionStatus("open");
    source.onerror = (e) => {
      setConnectionStatus("error");
      setError(e);
    };
    source.onmessage = (e) => setData(JSON.parse(e.data) as T);

    return () => source.close();
  }, [url]);

  return { data, connectionStatus, error };
}
