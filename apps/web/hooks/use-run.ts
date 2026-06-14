"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { approveRun, getRun, startRun } from "@/lib/api";
import { TERMINAL_STATUSES } from "@/lib/types";
import type { Decision, RunStatus, RunStatusValue } from "@/lib/types";

const POLL_MS = 1500;
// Statuses we keep polling; awaiting_approval and terminal statuses pause the loop.
const ACTIVE: RunStatusValue[] = ["queued", "running"];

/** Drives one run: start → poll every ~1.5s → pause at awaiting_approval/terminal. */
export function useRun() {
  const [run, setRun] = useState<RunStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [polling, setPolling] = useState(false);
  // A new target (or a bumped nonce on the same id) (re)starts the polling effect.
  // `resuming` is set after an approve: poll *through* awaiting_approval/running until a
  // terminal status, so a failed resume surfaces as "error" instead of stranding the panel.
  const [target, setTarget] = useState<{ id: string; nonce: number; resuming?: boolean } | null>(
    null,
  );
  const nonce = useRef(0);

  const handleError = useCallback((e: unknown) => {
    setError(e instanceof Error ? e.message : "request failed");
    setPolling(false);
  }, []);

  // The poll loop lives entirely inside the effect — no self-referencing callback.
  useEffect(() => {
    if (!target) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const poll = async () => {
      try {
        const r = await getRun(target.id);
        if (cancelled) return;
        setRun(r);
        // After an approve, keep polling until terminal (resume transitions
        // awaiting_approval → running → completed/error); otherwise pause at awaiting_approval.
        const keepGoing = target.resuming
          ? !TERMINAL_STATUSES.includes(r.status)
          : ACTIVE.includes(r.status);
        if (keepGoing) {
          timer = setTimeout(poll, POLL_MS);
        } else {
          setPolling(false); // nested in poll(), not the effect body
        }
      } catch (e) {
        if (!cancelled) handleError(e);
      }
    };

    void poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [target, handleError]);

  const start = useCallback(async (incidentId: string, dataMode: string) => {
    setError(null);
    setRun(null);
    setPolling(true);
    try {
      const { run_id } = await startRun(incidentId, dataMode);
      setTarget({ id: run_id, nonce: ++nonce.current });
    } catch (e) {
      handleError(e);
    }
  }, [handleError]);

  const approve = useCallback(
    async (decision: Decision, editedPlan?: string | null) => {
      const id = target?.id;
      if (!id) return;
      setPolling(true);
      try {
        const r = await approveRun(id, decision, editedPlan);
        setRun(r);
        setTarget({ id, nonce: ++nonce.current, resuming: true }); // re-poll to terminal status
      } catch (e) {
        handleError(e);
      }
    },
    [target, handleError],
  );

  /** Load an existing run by id (history replay); resumes polling if still active. */
  const load = useCallback(async (id: string) => {
    setError(null);
    setPolling(true);
    setTarget({ id, nonce: ++nonce.current });
  }, []);

  const reset = useCallback(() => {
    setTarget(null);
    setRun(null);
    setError(null);
    setPolling(false);
  }, []);

  return { run, error, polling, start, approve, load, reset };
}
