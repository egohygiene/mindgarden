import { useEffect, useRef, useState } from "react";

import type { GardenClient, StudioDiagnostics } from "./api";
import { DiagnosticsView, type DiagnosticEvent } from "./diagnostics";

const browserCapacity = 40;
const refreshInterval = 2_500;
const requestTimeout = 4_000;

export function useBrowserDiagnostics(enabled: boolean) {
  const [events, setEvents] = useState<DiagnosticEvent[]>([]);
  const nextId = useRef(1);

  useEffect(() => {
    if (!enabled) {
      setEvents([]);
      return;
    }
    function record(code: string, outcome: DiagnosticEvent["outcome"]) {
      const event: DiagnosticEvent = {
        id: nextId.current++,
        provider: "studio",
        source: "browser",
        operation: "console",
        outcome,
        code,
        at_ms: Date.now(),
        duration_ms: 0,
      };
      setEvents((previous) => [...previous.slice(1 - browserCapacity), event]);
    }

    // Keep DevTools intact. Only the level is captured for the visit log.
    const warn = console.warn;
    const error = console.error;
    const observedWarning: typeof console.warn = (...values: unknown[]) => {
      record("BROWSER_CONSOLE_WARNING", "attention");
      warn.apply(console, values);
    };
    const observedError: typeof console.error = (...values: unknown[]) => {
      record("BROWSER_CONSOLE_ERROR", "error");
      error.apply(console, values);
    };
    const runtimeError = () => record("BROWSER_RUNTIME_ERROR", "error");
    const rejection = () => record("BROWSER_UNHANDLED_REJECTION", "error");

    console.warn = observedWarning;
    console.error = observedError;
    window.addEventListener("error", runtimeError);
    window.addEventListener("unhandledrejection", rejection);
    return () => {
      if (console.warn === observedWarning) console.warn = warn;
      if (console.error === observedError) console.error = error;
      window.removeEventListener("error", runtimeError);
      window.removeEventListener("unhandledrejection", rejection);
    };
  }, [enabled]);

  return enabled ? events : [];
}

export function DiagnosticsPanel({ client, browserEvents }: {
  client: GardenClient;
  browserEvents: readonly DiagnosticEvent[];
}) {
  const [report, setReport] = useState<StudioDiagnostics>();
  const [error, setError] = useState(false);
  const [revision, refresh] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    async function load() {
      try {
        const signal = AbortSignal.any([controller.signal, AbortSignal.timeout(requestTimeout)]);
        const value = await client.diagnostics(signal);
        if (controller.signal.aborted) return;
        setReport(value);
        setError(false);
      } catch {
        if (controller.signal.aborted) return;
        setReport(undefined);
        setError(true);
      }
      if (!controller.signal.aborted) timer = setTimeout(() => void load(), refreshInterval);
    }

    void load();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [client, revision]);

  return <DiagnosticsView
    events={report ? [...report.events, ...browserEvents] : []}
    serverCapacity={report?.capacity ?? 80}
    loading={!report && !error}
    error={error}
    onRefresh={() => refresh((previous) => previous + 1)}
  />;
}
