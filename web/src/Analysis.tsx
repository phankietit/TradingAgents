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

const terminal = (status: string) => ['succeeded', 'failed', 'cancelled'].includes(status);

export default function Analysis() {
  const [version, setVersion] = useState(0);
  const catalog = useResource<Instrument[]>('/instruments?limit=500', 0, instruments);
  const history = useResource<Run[]>('/runs?limit=200', version);
  const [selected, setSelected] = useState<string | null>(null);
  const [observedStatuses, setObservedStatuses] = useState<Record<string, string>>({});
  const observeStatus = useCallback((id: string, status: string) => {
    setObservedStatuses(previous => previous[id] === status ? previous : { ...previous, [id]: status });
  }, []);
  const [initialInstrument, setInitialInstrument] = useState(() => new URLSearchParams(window.location.hash.split('?')[1]).get('instrument') ?? undefined);
  const [newRun, setNewRun] = useState(!!initialInstrument);
  const refresh = () => { setObservedStatuses({}); setVersion(value => value + 1); };
  const run = history.data?.find(item => item.run_id === selected) ?? history.data?.[0];
  return <>
    <div className="section-actions"><p className="muted">Snapshot-based research · Results require review, not automatic execution.</p>
      <button className="primary" onClick={() => setNewRun(true)}>New analysis</button><button onClick={refresh}>Refresh runs</button></div>
    {newRun && catalog.data ? <RunForm key={initialInstrument} catalog={catalog.data} initialInstrument={initialInstrument}
      onClose={() => setNewRun(false)} onCreated={value => { setSelected(value.run_id); setNewRun(false); refresh(); }} /> : null}
    {catalog.error ? <p role="alert" className="danger">Instrument discovery failed. {errorMessage(catalog.error)}</p> : null}
    <div className="market-layout">
      <section className="instrument-list" aria-label="Analysis history"><div className="list-heading">Recent runs <span>{history.data?.length ?? '—'}</span></div>
        {history.loading ? <p role="status">Loading runs…</p> : history.error ? <p role="alert" className="danger">{errorMessage(history.error)}</p>
          : !history.data?.length ? <p className="muted">No runs yet. Create one using saved evidence.</p>
          : <ul>{history.data.map(item => <li key={item.run_id}><button aria-pressed={run?.run_id === item.run_id} onClick={() => setSelected(item.run_id)}>
            <span className="instrument-row"><strong>{catalog.data?.find(asset => asset.instrument_id === item.instrument_id)?.canonical_symbol ?? 'Instrument'}</strong><span>{processingLabels[observedStatuses[item.run_id] ?? item.status] ?? 'Status unavailable'}</span></span>
            <span className="instrument-name">{timestamp(item.created_at)}</span>
          </button></li>)}</ul>}
        {history.data?.length === 200 ? <p className="warning">Showing the latest 200 runs.</p> : null}
      </section>
      {run ? <RunDetail key={run.run_id} runId={run.run_id} version={version} onStatus={observeStatus} onChanged={refresh} onRetry={value => { setInitialInstrument(value.instrument_id); setNewRun(true); }} />
        : <section className="empty-state"><h2>Research runs</h2><p>Queue a run to inspect progress and artifacts. A worker must be running to process the queue.</p></section>}
    </div>
  </>;
}

const eventNames = ['run.queued', 'run.started', 'stage.started', 'stage.completed', 'artifact.created', 'decision.ready', 'run.retrying', 'run.cancel_requested', 'run.cancelled', 'run.failed', 'run.succeeded'];
function RunDetail({ runId, version, onStatus, onChanged, onRetry }: { runId: string; version: number; onStatus: (id: string, status: string) => void; onChanged: () => void; onRetry: (run: Run) => void }) {
  const [tick, setTick] = useState(0);
  const run = useResource<Run>(`/runs/${encodeURIComponent(runId)}`, version + tick);
  const artifacts = useResource<Artifact[]>(`/runs/${encodeURIComponent(runId)}/artifacts?limit=200`, version + tick);
  const [events, setEvents] = useState<{ sequence: number; event_type: string; occurred_at: string }[]>([]);
  const [streamError, setStreamError] = useState(false);
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  const isTerminal = run.data ? terminal(run.data.status) : false;
  const observedStatus = run.data?.status;
  useEffect(() => {
    if (observedStatus) onStatus(runId, observedStatus);
  }, [runId, observedStatus, onStatus]);
  useEffect(() => {
    const stream = new EventSource(`/api/v1/runs/${encodeURIComponent(runId)}/events`);
    const update = (event: MessageEvent) => {
      try {
        const value = JSON.parse(event.data);
        if (!Number.isInteger(value.sequence) || typeof value.event_type !== 'string' || typeof value.occurred_at !== 'string') return;
        setEvents(previous => [...previous.filter(item => item.sequence !== value.sequence), { sequence: value.sequence, event_type: value.event_type, occurred_at: value.occurred_at }].sort((a, b) => a.sequence - b.sequence).slice(-100));
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
  return <section className="instrument-detail" aria-label="Run details">
    <h2>Research progress</h2>
    {run.error ? <p role="alert" className="danger">{errorMessage(run.error)}</p> : run.data ? <>
      <p role="status">Research: <strong>{processingLabels[run.data.status] ?? 'Status unavailable'}</strong> · As of {timestamp(run.data.analysis_as_of)}</p>
      <JobProgress runId={runId} version={version + tick} />
      {run.data.status === 'queued' ? <p className="notice">Waiting for a worker. Queued does not mean analysis has started.</p> : null}
      {run.data.error_code ? <><p className="notice danger">Research could not be completed. No investment conclusion is available from this run. Check the research service before configuring a new attempt.</p><details><summary>Failure details</summary><p className="mono">{run.data.error_code}</p></details></> : null}
      <p className="muted">Analysts: {run.data.selected_analysts.join(', ')} · {run.data.snapshot_ids.length} bound snapshots</p>
      {!isTerminal ? <button disabled={pending} onClick={cancel}>{pending ? 'Requesting cancellation…' : 'Cancel run'}</button> : ['failed', 'cancelled'].includes(run.data.status) ? <button onClick={() => onRetry(run.data!)}>Configure new attempt</button> : null}
    </> : <p role="status">Loading run…</p>}
    {error ? <p role="alert" className="danger">{error}</p> : null}
    {streamError ? <p className="warning">Event connection interrupted; active run status refreshes every 5 seconds.</p> : null}
    <details><summary>Processing timeline</summary><ol className="event-list">{events.map(event => <li key={event.sequence}><span>{eventLabel(event.event_type)}</span><time>{timestamp(event.occurred_at)}</time></li>)}</ol>
    {!events.length ? <p className="muted">No events received yet.</p> : null}
    </details>
    <h3>Reports & evidence</h3>
    {artifacts.error ? <p role="alert" className="danger">{errorMessage(artifacts.error)}</p> : artifacts.data?.length ? <ul className="artifact-list">{artifacts.data.map(item => <li key={item.artifact_id}>
      <a href={`/api/v1/artifacts/${encodeURIComponent(item.artifact_id)}`} download>{item.kind.replaceAll('_', ' ')} · Download</a>
      <details><summary>File details</summary><p className="muted">{item.media_type} · {item.byte_size.toLocaleString('en-US')} bytes · {timestamp(item.created_at)}</p><p className="mono caption">{item.content_hash}</p></details>
      <ArtifactPreview artifact={item} runId={runId} />
    </li>)}</ul> : <p className="muted">No artifacts have been published for this run.</p>}
    <p className="muted caption">Artifacts download after backend integrity checks. Run success does not imply decision approval.</p>
  </section>;
}
