import { ApiError, errorMessage } from './api';
import { timestamp, useResource } from './data';

export const processingLabels: Record<string, string> = {
  queued: 'Waiting to start', running: 'In progress', retry_wait: 'Waiting to retry',
  cancel_requested: 'Cancellation requested', succeeded: 'Research complete', failed: 'Research failed', cancelled: 'Cancelled',
};
interface JobState { job_id: string; run_id: string; status: string; attempt: number; max_attempts: number;
  available_at: string; updated_at: string; completed_at: string | null }
function validate(value: JobState): JobState {
  const date = (value: unknown) => typeof value === 'string' && Number.isFinite(Date.parse(value));
  if (!value || typeof value.job_id !== 'string' || typeof value.run_id !== 'string'
    || !Object.hasOwn(processingLabels, value.status) || !Number.isInteger(value.attempt) || value.attempt < 0
    || !Number.isInteger(value.max_attempts) || value.max_attempts < 1 || value.max_attempts > 20 || value.attempt > value.max_attempts
    || !date(value.available_at) || !date(value.updated_at) || (value.completed_at !== null && !date(value.completed_at))) throw new ApiError(502);
  return value;
}

export default function JobProgress({runId, version}: {runId: string; version: number}) {
  const job = useResource<JobState>(`/runs/${encodeURIComponent(runId)}/job`, version, validate);
  if (job.loading) return <p role="status">Checking processing status…</p>;
  if (job.error || !job.data || job.data.run_id !== runId) return <p className="warning">Processing details unavailable. {job.error instanceof ApiError && job.error.status === 404 ? 'No processing record was found for this research.' : errorMessage(job.error)} This does not confirm that research is running.</p>;
  const data = job.data;
  return <section aria-label="Processing status">
    <p><strong>{processingLabels[data.status]}</strong> · {data.attempt === 0 ? 'No attempt started' : `Attempt ${data.attempt} of ${data.max_attempts}`}</p>
    {data.status === 'retry_wait' ? <p className="notice">A retry is scheduled no earlier than {timestamp(data.available_at)}. It starts only when a background service is available and may incur further model charges.</p> : null}
    {data.status === 'cancel_requested' ? <p className="notice">Cancellation is pending. Work may continue until the current processing step stops.</p> : null}
    <details><summary>Processing details</summary><dl><dt>Last updated</dt><dd>{timestamp(data.updated_at)}</dd>
      {data.completed_at ? <><dt>Finished</dt><dd>{timestamp(data.completed_at)}</dd></> : null}
      <dt>Processing ID</dt><dd className="mono">{data.job_id}</dd><dt>Research ID</dt><dd className="mono">{data.run_id}</dd>
    </dl></details>
  </section>;
}
