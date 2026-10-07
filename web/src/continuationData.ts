import { ApiError, request } from './api';
import type { ResearchEvent } from './ResearchWorkflow';

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const statuses = ['reserved', 'leased', 'cancel_requested', 'cancelled', 'review_required', 'completed'];
export interface Continuation {
  run_id: string; execution_id: string; attempt: number; status: string;
  preparation_requires_review: boolean; lease_expired: boolean;
  report_artifact_id: string | null; evidence_artifact_id: string | null; decision_id: string | null;
  local_stop?: {stopped_at: string; continuation_authorized: false; provider_cost_known: false} | null;
}
export interface Discovery { items: Continuation[]; has_more: boolean }
export interface Preparation { run_id: string; observation_hash: string; remaining_wall_seconds: number;
  remaining_model_calls: number; dispatch_enabled: false; disclosures: string[] }
export interface Progress { events: ResearchEvent[]; has_more: boolean; approval_eligible: false }
function reject(): never { throw new ApiError(502); }
export function continuation(value: Continuation, runId: string): Continuation {
  if (!value || value.run_id !== runId || !uuid.test(value.execution_id) || !statuses.includes(value.status)
    || !Number.isSafeInteger(value.attempt) || value.attempt < 2 || value.attempt > 1_000_000
    || typeof value.preparation_requires_review !== 'boolean' || typeof value.lease_expired !== 'boolean'
    || [value.report_artifact_id, value.evidence_artifact_id, value.decision_id].some(id => id !== null && (typeof id !== 'string' || !uuid.test(id)))) reject();
  if (value.status === 'completed') {
    if (!value.report_artifact_id || !value.decision_id || value.preparation_requires_review) reject();
  } else if (value.report_artifact_id || value.evidence_artifact_id || value.decision_id) reject();
  if (value.local_stop != null) {
    const stop = value.local_stop;
    if (!['cancel_requested', 'review_required'].includes(value.status) && !(value.status === 'leased' && value.lease_expired)) reject();
    if (typeof stop !== 'object' || Array.isArray(stop) || typeof stop.stopped_at !== 'string'
      || !/^\d{4}-\d{2}-\d{2}T.+(?:Z|[+-]\d{2}:\d{2})$/.test(stop.stopped_at) || !Number.isFinite(Date.parse(stop.stopped_at))
      || stop.continuation_authorized !== false || stop.provider_cost_known !== false
      || Object.keys(stop).sort().join('|') !== 'continuation_authorized|provider_cost_known|stopped_at') reject();
  }
  return value;
}
export function discovery(value: Discovery, runId: string): Discovery {
  if (!value || !Array.isArray(value.items) || value.items.length > 50 || typeof value.has_more !== 'boolean'
    || (value.has_more && !value.items.length)) reject();
  value.items.forEach(item => continuation(item, runId));
  if (new Set(value.items.map(item => item.execution_id)).size !== value.items.length
    || value.items.some((item, index) => index > 0 && item.attempt >= value.items[index - 1].attempt)) reject();
  return value;
}
export function preparation(value: Preparation, runId: string): Preparation {
  if (!value || value.run_id !== runId || !/^[a-f0-9]{64}$/.test(value.observation_hash)
    || !Number.isFinite(value.remaining_wall_seconds) || value.remaining_wall_seconds < 0
    || !Number.isSafeInteger(value.remaining_model_calls) || value.remaining_model_calls < 0
    || value.dispatch_enabled !== false || !Array.isArray(value.disclosures)
    || value.disclosures.join('|') !== 'original_allowance_retained|provider_cost_unknown|prior_research_unvalidated') reject();
  return value;
}
export function progress(value: Progress, attempt: number): Progress {
  const types = ['research.execution_started', 'stage.started', 'stage.completed', 'model.usage', 'artifact.created', 'decision.ready'];
  if (!value || value.approval_eligible !== false || typeof value.has_more !== 'boolean'
    || (value.has_more && !value.events?.length)
    || !Array.isArray(value.events) || value.events.length > 100 || value.events.some((event, index) => !event
      || !Number.isSafeInteger(event.sequence) || event.sequence < 1 || !types.includes(event.event_type)
      || event.attempt !== attempt || !Number.isFinite(Date.parse(event.occurred_at))
      || (event.stage != null && (typeof event.stage !== 'string' || event.stage.length > 80))
      || (index > 0 && event.sequence <= value.events[index - 1].sequence))) reject();
  return value;
}

/** Consume every page, then publish one complete display projection. Incremental
 * polling starts after the last validated sequence, never a guessed page count. */
export async function readProgress(path: string, attempt: number, signal: AbortSignal,
  previous: readonly ResearchEvent[] = []): Promise<Progress> {
  const events = [...previous];
  let cursor = events.at(-1)?.sequence ?? 0;
  while (true) {
    signal.throwIfAborted();
    const page = progress(await request<Progress>(cursor ? `${path}?after_sequence=${cursor}` : path,
      {signal}, 128 * 1024), attempt);
    signal.throwIfAborted();
    if (page.events.some(event => event.sequence <= cursor)) reject();
    events.push(...page.events);
    if (!page.has_more) return {events, has_more:false, approval_eligible:false};
    cursor = events.at(-1)!.sequence;
  }
}
