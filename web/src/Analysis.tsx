import { t, useLocale } from './i18n';
import { useCallback, useEffect, useState } from 'react';
import { errorMessage, mutate } from './api';
import { instruments, timestamp, useResource } from './data';
import type { Instrument } from './data';
import RunForm from './RunForm';
import type { Run } from './RunForm';
import ArtifactPreview from './ArtifactPreview';
import type { Artifact } from './ArtifactPreview';
import JobProgress, { processingLabels } from './JobProgress';
import { eventLabel } from './financialLabels';
import { researchLabel } from './researchLabels';
import ResearchWorkflow, { type ResearchEvent } from './ResearchWorkflow';

const terminal = (status: string) => ['succeeded', 'failed', 'cancelled'].includes(status);

export default function Analysis() {
  useLocale();
  const [version, setVersion] = useState(0);
  const catalog = useResource<Instrument[]>('/instruments?limit=500', 0, instruments);
  const history = useResource<Run[]>('/runs?limit=200', version);
  const [selected, setSelected] = useState<string | null>(() => new URLSearchParams(window.location.hash.split('?')[1]).get('run'));
  const [observedStatuses, setObservedStatuses] = useState<Record<string, string>>({});
  const observeStatus = useCallback((id: string, status: string) => {
    setObservedStatuses(previous => previous[id] === status ? previous : { ...previous, [id]: status });
  }, []);
  const [initialInstrument, setInitialInstrument] = useState(() => new URLSearchParams(window.location.hash.split('?')[1]).get('instrument') ?? undefined);
  const [newRun, setNewRun] = useState(!!initialInstrument);
  const refresh = () => { setObservedStatuses({}); setVersion(value => value + 1); };
  const runId = selected ?? history.data?.[0]?.run_id;
  const selectRun = (id: string) => { setSelected(id); window.history.replaceState(null, '', `#/analysis?run=${encodeURIComponent(id)}`); };
  return <>
    <div className="section-actions"><p className="muted">{t("Snapshot-based research · Results require review, not automatic execution.")}</p>
      {!newRun ? <><button className="primary" onClick={() => setNewRun(true)}>{t("New analysis")}</button><button onClick={refresh}>{t("Refresh runs")}</button></> : null}</div>
    {newRun && catalog.data ? <RunForm key={initialInstrument} catalog={catalog.data} initialInstrument={initialInstrument}
      onClose={() => { setNewRun(false); window.history.replaceState(null, '', runId ? `#/analysis?run=${encodeURIComponent(runId)}` : '#/analysis'); }} onCreated={value => {
        setSelected(value.run_id); setNewRun(false); window.history.replaceState(null, '', `#/analysis?run=${encodeURIComponent(value.run_id)}`); refresh();
      }} /> : null}
    {catalog.error ? <p role="alert" className="danger">{t("Instrument discovery failed.")} {t(errorMessage(catalog.error))}</p> : null}
    {!newRun ? <div className="market-layout research-workspace">
      <section className="instrument-list" aria-label={t("Analysis history")}><div className="list-heading">{t("Recent runs")} <span>{history.data?.length ?? '—'}</span></div>
        {history.data?.length ? <label className="compact-run-picker">{t('Select analysis')}
          <select value={runId ?? ''} onChange={event => selectRun(event.target.value)}>
            {runId && !history.data.some(item => item.run_id === runId) ? <option value={runId}>{t('Selected analysis')}</option> : null}
            {history.data.map(item => <option key={item.run_id} value={item.run_id}>
              {catalog.data?.find(asset => asset.instrument_id === item.instrument_id)?.canonical_symbol ?? t('Instrument')} · {timestamp(item.created_at)}
            </option>)}
          </select></label> : null}
        {history.loading ? <p role="status">{t("Loading runs…")}</p> : history.error ? <p role="alert" className="danger">{t(errorMessage(history.error))}</p>
          : !history.data?.length ? <p className="muted">{t("No runs yet. Create one using saved evidence.")}</p>
          : <ul className="desktop-run-history">{history.data.map(item => <li key={item.run_id}><button aria-pressed={runId === item.run_id} onClick={() => selectRun(item.run_id)}>
            <span className="instrument-row"><strong>{catalog.data?.find(asset => asset.instrument_id === item.instrument_id)?.canonical_symbol ?? t("Instrument")}</strong><span>{t(processingLabels[observedStatuses[item.run_id] ?? item.status] ?? 'Status unavailable')}</span></span>
            <span className="instrument-name">{timestamp(item.created_at)}</span>
          </button></li>)}</ul>}
        {history.data?.length === 200 ? <p className="warning">{t("Showing the latest 200 runs.")}</p> : null}
      </section>
      {runId ? <RunDetail key={runId} runId={runId} version={version} onStatus={observeStatus} onChanged={refresh} onRetry={value => { setInitialInstrument(value.instrument_id); setNewRun(true); }} />
        : <section className="empty-state"><h2>{t("Research runs")}</h2><p>{t("Queue a run to inspect progress and artifacts. A worker must be running to process the queue.")}</p></section>}
    </div> : null}
  </>;
}

const eventNames = ['run.queued', 'run.started', 'stage.started', 'stage.completed', 'model.usage', 'artifact.created', 'decision.ready', 'run.retrying', 'run.cancel_requested', 'run.cancelled', 'run.failed', 'run.succeeded'];
function RunDetail({ runId, version, onStatus, onChanged, onRetry }: { runId: string; version: number; onStatus: (id: string, status: string) => void; onChanged: () => void; onRetry: (run: Run) => void }) {
  useLocale();
  const [tick, setTick] = useState(0);
  const run = useResource<Run>(`/runs/${encodeURIComponent(runId)}`, version + tick, undefined, true);
  const artifacts = useResource<Artifact[]>(`/runs/${encodeURIComponent(runId)}/artifacts?limit=200`, version + tick, undefined, true);
  const [events, setEvents] = useState<ResearchEvent[]>([]);
  const [streamError, setStreamError] = useState(false);
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const isTerminal = run.data ? terminal(run.data.status) : false;
  const observedStatus = jobStatus ?? run.data?.status;
  useEffect(() => {
    if (observedStatus) onStatus(runId, observedStatus);
  }, [runId, observedStatus, onStatus]);
  useEffect(() => {
    const stream = new EventSource(`/api/v1/runs/${encodeURIComponent(runId)}/events`);
    const update = (event: MessageEvent) => {
      try {
        const value = JSON.parse(event.data);
        if (!Number.isInteger(value.sequence) || typeof value.event_type !== 'string' || typeof value.occurred_at !== 'string') return;
        const stage = typeof value.payload?.stage === 'string' && value.payload.stage.length < 80 ? value.payload.stage : undefined;
        const attempt = Number.isInteger(value.payload?.attempt) && value.payload.attempt > 0 ? value.payload.attempt : undefined;
        setEvents(previous => [...previous.filter(item => item.sequence !== value.sequence), { sequence: value.sequence, event_type: value.event_type, occurred_at: value.occurred_at, stage, attempt }].sort((a, b) => a.sequence - b.sequence).slice(-100));
        if (['run.succeeded', 'run.failed', 'run.cancelled'].includes(value.event_type)) stream.close();
        setTick(value => value + 1);
      } catch { setStreamError(true); }
    };
    eventNames.forEach(name => stream.addEventListener(name, update as EventListener));
    stream.onopen = () => setStreamError(false);
    stream.onerror = () => setStreamError(true);
    return () => stream.close();
  }, [runId]);
  useEffect(() => {
    if (isTerminal) return;
    const timer = window.setInterval(() => setTick(value => value + 1), 5000);
    return () => window.clearInterval(timer);
  }, [isTerminal]);
  async function cancel() {
    setPending(true); setError('');
    try { await mutate(`/runs/${encodeURIComponent(runId)}/cancel`); setTick(value => value + 1); onChanged(); }
    catch (cause) { setError(errorMessage(cause)); }
    finally { setPending(false); }
  }
  return <section className="instrument-detail" aria-label={t("Run details")}>
    <h2>{t("Research progress")}</h2>
    {run.error ? <p role="alert" className="danger">{t(errorMessage(run.error))}</p> : run.data ? <>
      <p className="muted caption">{t("As of")} {timestamp(run.data.analysis_as_of)}</p>
      <ResearchWorkflow events={events} status={jobStatus ?? run.data.status} hasSources={run.data.snapshot_ids.length > 0}
        hasReport={artifacts.data?.some(item => item.kind === 'analysis_report') ?? false} />
      <JobProgress runId={runId} version={version + tick} onStatus={setJobStatus} />
      {run.data.error_code ? <><p className="notice danger">{t("Research could not be completed. No investment conclusion is available from this run. Check the research service before configuring a new attempt.")}</p><details><summary>{t("Failure details")}</summary><p className="mono">{run.data.error_code}</p></details></> : null}
      <p className="muted caption">{t("Research coverage:")} {run.data.selected_analysts.map(researchLabel).join(', ')} · {run.data.snapshot_ids.length}  {t("saved sources")}</p>
      {!isTerminal ? <button disabled={pending} onClick={cancel}>{pending ? t("Requesting cancellation…") : t("Cancel run")}</button> : ['failed', 'cancelled'].includes(run.data.status) ? <button onClick={() => onRetry(run.data!)}>{t("Configure new attempt")}</button> : null}
    </> : <p role="status">{t("Loading run…")}</p>}
    {error ? <p role="alert" className="danger">{t(error)}</p> : null}
    {streamError ? <p className="warning">{t("Event connection interrupted; active run status refreshes every 5 seconds.")}</p> : null}
    <details><summary>{t("Processing timeline")}</summary><ol className="event-list">{events.map(event => <li key={event.sequence}><span>{eventLabel(event.event_type)}{event.stage ? ` · ${t(event.stage)}` : ''}</span><time>{timestamp(event.occurred_at)}</time></li>)}</ol>
    {!events.length ? <p className="muted">{t("No events received yet.")}</p> : null}
    </details>
    <h3>{t("Reports & evidence")}</h3>
    {artifacts.error ? <p role="alert" className="danger">{t(errorMessage(artifacts.error))}</p> : artifacts.data?.length ? <ul className="artifact-list">{artifacts.data.map(item => <li key={item.artifact_id}>
      <ArtifactPreview artifact={item} runId={runId} embedded={item.kind === 'analysis_report'} />
      <details><summary>{t("File details")}</summary><a href={`/api/v1/artifacts/${encodeURIComponent(item.artifact_id)}`} download>{t(item.kind.replaceAll('_', ' '))} {t("· Download")}</a><p className="muted">{item.media_type} · {item.byte_size.toLocaleString('en-US')} {t("bytes ·")} {timestamp(item.created_at)}</p><p className="mono caption">{item.content_hash}</p></details>
    </li>)}</ul> : <p className="muted">{t("No artifacts have been published for this run.")}</p>}
    <p className="muted caption">{t("Artifacts download after backend integrity checks. Run success does not imply decision approval.")}</p>
  </section>;
}
