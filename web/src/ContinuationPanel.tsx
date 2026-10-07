import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError, errorMessage, mutate } from './api';
import { useResource } from './data';
import { t, useLocale } from './i18n';
import { continuation, discovery, preparation } from './continuationData';
import type { Continuation, Discovery, Preparation } from './continuationData';
import { useContinuationProgress } from './useContinuationProgress';
import ResearchWorkflow from './ResearchWorkflow';

const labels: Record<string, string> = { reserved: 'Continuation saved', leased: 'Continuing research',
  cancel_requested: 'Stopping continuation', cancelled: 'Continuation cancelled',
  review_required: 'Continuation needs review', completed: 'Continuation report available' };
const acknowledgments = [
  'I understand this uses only the original remaining allowance.',
  'I understand provider charges may continue and the cost is unknown.',
  'I understand saved working notes are unvalidated and do not approve a decision.',
];

/** Explicit owner consent only; no automatic preparation, reservation or retry. */
export default function ContinuationPanel({runId, version, onReports, onNewAttempt}: {
  runId: string; version: number; onReports: (ids: string[]) => void; onNewAttempt: () => void;
}) {
  useLocale();
  const [tick, setTick] = useState(0);
  const [before, setBefore] = useState<number | null>(null);
  const [selected, setSelected] = useState('');
  const [prepared, setPrepared] = useState<Preparation | null>(null);
  const [confirmed, setConfirmed] = useState([false, false, false]);
  const [pending, setPending] = useState('');
  const [error, setError] = useState('');
  const idempotency = useRef<string | null>(null);
  const validateDiscovery = useCallback((value: Discovery) => discovery(value, runId), [runId]);
  const data = useResource<Discovery>(`/runs/${encodeURIComponent(runId)}/continuations?limit=20${before === null ? '' : `&before_attempt=${before}`}`,
    version + tick, validateDiscovery, true);
  const current = data.data?.items.find(item => item.execution_id === selected) ?? data.data?.items[0];
  const active = !!data.data?.items.some(item => ['reserved', 'leased', 'cancel_requested'].includes(item.status)
    && !item.preparation_requires_review && !item.lease_expired);
  const attempt = current?.attempt ?? 0;
  const events = useContinuationProgress(current ? `/runs/${encodeURIComponent(runId)}/continuations/${current.execution_id}/events` : null,
    attempt, version + tick);
  const reportId = current?.status === 'completed' ? current.report_artifact_id ?? '' : '';
  useEffect(() => { onReports(reportId ? [reportId] : []); }, [reportId, onReports]);
  useEffect(() => {
    if (!active) return;
    const timer = window.setInterval(() => setTick(value => value + 1), 5000);
    return () => window.clearInterval(timer);
  }, [active]);
  async function prepare() {
    setPending('prepare'); setError(''); setPrepared(null); setConfirmed([false, false, false]);
    try {
      const value = preparation(await mutate<Preparation>(`/runs/${encodeURIComponent(runId)}/continuation/prepare`), runId);
      idempotency.current = crypto.randomUUID(); setPrepared(value);
    } catch (cause) { setError(errorMessage(cause)); }
    finally { setPending(''); }
  }
  async function reserve(event: React.FormEvent) {
    event.preventDefault();
    if (!prepared || !confirmed.every(Boolean) || !idempotency.current || pending) return;
    setPending('reserve'); setError('');
    try {
      const value = await mutate<{run_id: string; execution_id: string; status: string; dispatch_enabled: false}>(
        `/runs/${encodeURIComponent(runId)}/continuations`, {observation_hash: prepared.observation_hash,
          idempotency_key: idempotency.current, confirm_continue: true, acknowledge_original_allowance: confirmed[0],
          acknowledge_unknown_provider_cost: confirmed[1], acknowledge_unvalidated_prior_research: confirmed[2]});
      if (value.run_id !== runId || value.dispatch_enabled !== false || value.status !== 'reserved'
        || typeof value.execution_id !== 'string' || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value.execution_id)) throw new ApiError(502);
      setSelected(value.execution_id); setPrepared(null); setBefore(null); setTick(value => value + 1);
    } catch (cause) { setError(errorMessage(cause)); setTick(value => value + 1); }
    finally { setPending(''); }
  }
  async function cancel(item: Continuation) {
    setPending('cancel'); setError('');
    try { continuation(await mutate<Continuation>(`/runs/${encodeURIComponent(runId)}/continuations/${item.execution_id}/cancel`), runId); setTick(value => value + 1); }
    catch (cause) { setError(errorMessage(cause)); }
    finally { setPending(''); }
  }
  const needsReview = current && (current.preparation_requires_review || (current.lease_expired && current.status !== 'completed') || current.status === 'review_required');
  const completed = current?.status === 'completed' && !needsReview;
  const controls = <>
    <p className="muted">{t('The original attempt stays unchanged. A continuation uses its saved context and remaining allowance, not a fresh analysis.')}</p>
    {current ? <>
      <label>{t('Saved continuation')}<select value={current.execution_id} onChange={event => setSelected(event.target.value)}>
        {data.data!.items.map(item => <option key={item.execution_id} value={item.execution_id}>{t('Attempt')} {item.attempt} · {t(labels[item.status])}</option>)}
      </select></label>
      {needsReview ? <p className="notice warning">{t('Processing could not continue safely. Do not assume it is still running or retry it automatically.')}</p>
        : current.status === 'reserved' ? <p className="notice">{t('Your continuation is saved. Processing starts only when the local continuation service is enabled. Do not submit a duplicate request.')}</p>
          : current.status === 'cancel_requested' ? <p className="notice">{t('Stopping has been requested. Provider work and charges may continue until the current step stops.')}</p> : null}
      {current.status === 'completed' ? null : <ResearchWorkflow
        events={events.data?.events ?? []} status={needsReview ? 'failed' : current.status === 'leased' ? 'running' : current.status}
        hasSources={true} hasReport={false} />}
      {events.error ? <p className="warning">{t('Continuation progress is unavailable. This does not confirm processing is running.')}</p> : null}
      {events.loading ? <p role="status" className="muted">{t('Loading continuation progress…')}</p> : null}
      {['reserved', 'leased', 'cancel_requested'].includes(current.status) && !needsReview ? <button disabled={!!pending}
        onClick={() => cancel(current)}>{t(pending === 'cancel' ? 'Requesting cancellation…' : 'Stop continuation')}</button> : null}
    </> : null}
    {data.loading ? <p role="status">{t('Checking saved continuation…')}</p> : null}
    {data.error ? <p className="warning">{t('Saved continuation could not be verified. Refresh before trying again.')}</p> : null}
    {error ? <p role="alert" className="danger">{t(error)} {t('Check saved continuations before resubmitting; a request may already have been saved.')}</p> : null}
    {prepared ? <form onSubmit={reserve} className="continuation-consent">
      <h3>{t('Review before continuing')}</h3>
      <p>{t('Remaining allowance:')} {Math.floor(prepared.remaining_wall_seconds / 60)} {t('minutes')} · {prepared.remaining_model_calls} {t('model calls')}</p>
      {acknowledgments.map((label, index) => <label key={label} className="continuation-check"><input type="checkbox" required disabled={!!pending}
        checked={confirmed[index]} onChange={event => setConfirmed(previous => previous.map((value, position) => position === index ? event.target.checked : value))} />{t(label)}</label>)}
      <div className="section-actions"><button className="primary" disabled={!!pending || !confirmed.every(Boolean) || prepared.remaining_model_calls < 1 || prepared.remaining_wall_seconds <= 0}>{t(pending === 'reserve' ? 'Saving continuation…' : 'Confirm and continue')}</button>
        <button type="button" disabled={!!pending} onClick={() => setPrepared(null)}>{t('Back')}</button></div>
    </form> : <div className="section-actions">
      {!active && !current && !data.error && !data.loading ? <button className="primary" disabled={!!pending} onClick={prepare}>{t(pending === 'prepare' ? 'Checking saved context…' : 'Check saved continuation')}</button> : null}
      <button disabled={!!pending} onClick={() => { setBefore(null); setSelected(''); setTick(value => value + 1); }}>{t('Refresh continuation')}</button>
      {!active && current?.status !== 'completed' ? <button disabled={!!pending} onClick={onNewAttempt}>{t('Configure new attempt')}</button> : null}
    </div>}
    {data.data?.has_more ? <button disabled={!!pending} onClick={() => { setBefore(data.data!.items.at(-1)!.attempt); setSelected(''); }}>{t('Older saved continuations')}</button> : null}
  </>;
  return <section className={`continuation-panel${completed ? ' continuation-completed' : ''}`} aria-label={t('Saved research continuation')}>
    <p className="eyebrow">{t('SAVED RESEARCH')}</p>
    <h2>{t(current ? needsReview ? 'Continuation needs review' : labels[current.status] : 'Research stopped before completion')}</h2>
    {completed ? <>
      <p className="notice">{t('Read the new report below. Completion does not mean its conclusions or a portfolio decision have been approved.')}</p>
      <details className="continuation-details"><summary>{t('Continuation details')}</summary>{controls}</details>
    </> : controls}
  </section>;
}
