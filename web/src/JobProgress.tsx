import { t, useLocale } from './i18n';
import { ApiError, errorMessage } from './api';
import { timestamp, useResource } from './data';
import { useEffect } from 'react';

export const processingLabels: Record<string, string> = {
  queued: 'Waiting to start', running: 'In progress', retry_wait: 'Waiting to retry',
  cancel_requested: 'Cancellation requested', succeeded: 'Processing complete', failed: 'Research failed', cancelled: 'Cancelled',
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

export default function JobProgress({runId, version, onStatus}: {runId: string; version: number; onStatus?: (status: string | null) => void}) {
  useLocale();
  const job = useResource<JobState>(`/runs/${encodeURIComponent(runId)}/job`, version, validate, true);
  const currentStatus = job.data?.run_id === runId ? job.data.status : undefined;
  // A failed or identity-mismatched refresh must also withdraw the parent's
  // previous observation, not just hide this component's status label.
  useEffect(() => { onStatus?.(currentStatus ?? null); }, [currentStatus, onStatus]);
  if (job.loading) return <p role="status">{t("Checking processing status…")}</p>;
  if (job.error || !job.data || job.data.run_id !== runId) return <p className="warning">{t("Processing details unavailable.")} {job.error instanceof ApiError && job.error.status === 404 ? t("No processing record was found for this research.") : t(errorMessage(job.error))}  {t("This does not confirm that research is running.")}</p>;
  const data = job.data;
  return <section aria-label={t("Processing status")}>
    <p><strong>{t(processingLabels[data.status])}</strong> · {data.attempt === 0 ? t("No attempt started") : `${t("Attempt")} ${data.attempt} ${t("of")} ${data.max_attempts}`}</p>
    {data.status === 'queued' ? <p className="notice">{t('Your request is saved, but AI processing has not started. The local analysis worker must be running. Do not submit a duplicate request.')}</p> : null}
    {data.status === 'retry_wait' ? <p className="notice">{t("A retry is scheduled no earlier than")} {timestamp(data.available_at)}{t(". It starts only when a background service is available and may incur further model charges.")}</p> : null}
    {data.status === 'cancel_requested' ? <p className="notice">{t("Cancellation is pending. Work may continue until the current processing step stops.")}</p> : null}
    <details><summary>{t("Processing details")}</summary><dl><dt>{t("Last updated")}</dt><dd>{timestamp(data.updated_at)}</dd>
      {data.completed_at ? <><dt>{t("Finished")}</dt><dd>{timestamp(data.completed_at)}</dd></> : null}
      <dt>{t("Processing ID")}</dt><dd className="mono">{data.job_id}</dd><dt>{t("Research ID")}</dt><dd className="mono">{data.run_id}</dd>
    </dl></details>
  </section>;
}
