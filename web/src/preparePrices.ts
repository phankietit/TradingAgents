import { ApiError, mutate } from './api';
import type { Snapshot } from './data';

export interface Prepared {
  status: string; snapshot: Snapshot | null; analysis_as_of: string; reused: boolean;
  retry_after_seconds?: number; last_failure?: string | null;
  checks?: number;
}
export interface PreparationProgress { attempt: number; remaining: number; waiting: boolean; reason?: string }
const retryable = new Set(['stale', 'coverage_gap', 'no_data', 'unavailable', 'rate_limited', 'cooldown', 'busy']);

function pause(signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    signal.throwIfAborted();
    const abort = () => { clearTimeout(timer); signal.removeEventListener('abort', abort); reject(signal.reason); };
    const timer = setTimeout(() => { signal.removeEventListener('abort', abort); resolve(); }, 1000);
    signal.addEventListener('abort', abort, { once: true });
  });
}

/** Three bounded checks; server cooldown is respected, never a tight polling loop. */
export async function preparePrices(instrumentId: string, signal: AbortSignal,
  progress: (value: PreparationProgress) => void): Promise<Prepared> {
  let result: Prepared;
  let lastFailure: string | undefined;
  for (let attempt = 1; attempt <= 3; attempt++) {
    signal.throwIfAborted();
    progress({ attempt, remaining: 0, waiting: false });
    try {
      const requestSignal = AbortSignal.any([signal, AbortSignal.timeout(60_000)]);
      result = await mutate<Prepared>(`/instruments/${encodeURIComponent(instrumentId)}/prepare-data`, undefined, 'POST', {}, requestSignal);
    } catch (error) {
      signal.throwIfAborted();
      if (!(error instanceof ApiError) || ![0, 429, 502, 503, 504].includes(error.status)) throw error;
      result = { status: error.status === 429 ? 'rate_limited' : 'unavailable', snapshot: null, analysis_as_of: '', reused: false };
    }
    signal.throwIfAborted();
    lastFailure = result.last_failure ?? (result.status === 'cooldown' ? lastFailure : result.status);
    if (result.status === 'ready' || !retryable.has(result.status)) return { ...result, checks: attempt };
    if (attempt === 3) return { ...result, last_failure: lastFailure, checks: attempt };
    const hint = result.retry_after_seconds;
    if (hint !== undefined && (!Number.isInteger(hint) || hint < 0 || hint > 120)) throw new ApiError(502);
    const seconds = Math.max(attempt * 60, hint ?? 0);
    const deadline = Date.now() + seconds * 1000;
    while (Date.now() < deadline) {
      progress({ attempt, remaining: Math.ceil((deadline - Date.now()) / 1000), waiting: true, reason: result.status });
      await pause(signal);
    }
  }
  throw new ApiError(502);
}
