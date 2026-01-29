// Module: data fetching for the map with optional polling and soft errors.
// Invariants: keep last good data on errors, update lastUpdated only on success.

import { useEffect, useRef, useState } from "react";

import { fetchMap, MapResponse } from "./api";

type UseMapPollingOptions = {
  enabled: boolean;
  pollIntervalMs?: number;
};

type MapPollingState = {
  data: MapResponse | null;
  error: string | null;
  lastUpdated: Date | null;
};

export function useMapPolling({ enabled, pollIntervalMs }: UseMapPollingOptions): MapPollingState {
  const [data, setData] = useState<MapResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const inFlightRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!enabled) return;

    let mounted = true;
    let intervalId: ReturnType<typeof setInterval> | null = null;

    const runFetch = async () => {
      // Abort previous request to prevent stale data from overwriting fresh data.
      if (inFlightRef.current) {
        inFlightRef.current.abort();
      }

      const controller = new AbortController();
      inFlightRef.current = controller;

      try {
        const res = await fetchMap(controller.signal);
        if (!mounted) return;
        setData(res);
        setError(null);
        setLastUpdated(new Date());
      } catch (err) {
        if (!mounted) return;
        if (controller.signal.aborted) return;
        console.error(err);
        // Soft error: keep last good data and lastUpdated unchanged.
        setError(String(err));
      }
    };

    runFetch();

    if (pollIntervalMs && pollIntervalMs > 0) {
      // Polling uses a single interval and is cleared on cleanup.
      intervalId = setInterval(runFetch, pollIntervalMs);
    }

    return () => {
      mounted = false;
      if (intervalId) clearInterval(intervalId);
      // Abort is required so late responses do not race and set state after unmount.
      if (inFlightRef.current) {
        inFlightRef.current.abort();
        inFlightRef.current = null;
      }
    };
  }, [enabled, pollIntervalMs]);

  return { data, error, lastUpdated };
}
