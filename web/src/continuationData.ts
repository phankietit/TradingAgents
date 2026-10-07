import { ApiError } from './api';
import type { ResearchEvent } from './ResearchWorkflow';

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const statuses = ['reserved', 'leased', 'cancel_requested', 'cancelled', 'review_required', 'completed'];
export interface Continuation {
  run_id: string; execution_id: string; attempt: number; status: string;
  preparation_requires_review: boolean; lease_expired: boolean;
  report_artifact_id: string | null; evidence_artifact_id: string | null; decision_id: string | null;
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
  return value;
}
export function discovery(value: Discovery, runId: string): Discovery {
  if (!value || !Array.isArray(value.items) || value.items.length > 50 || typeof value.has_more !== 'boolean') reject();
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
    || !Array.isArray(value.events) || value.events.length > 100 || value.events.some((event, index) => !event
      || !Number.isSafeInteger(event.sequence) || event.sequence < 1 || !types.includes(event.event_type)
      || event.attempt !== attempt || !Number.isFinite(Date.parse(event.occurred_at))
      || (event.stage != null && (typeof event.stage !== 'string' || event.stage.length > 80))
      || (index > 0 && event.sequence <= value.events[index - 1].sequence))) reject();
  return value;
}
