import { useEffect, useRef, useState } from 'react';
import { errorMessage, mutate } from './api';
import { instruments, percent, timestamp, useResource } from './data';
import type { Instrument } from './data';
import type { Run } from './RunForm';

interface Check { check_id: string; policy_id: string; policy_version: string; result: string; blocking: boolean; reason: string; observed_value: unknown; limit_value: unknown }
interface Evidence { evidence_id: string; snapshot_id: string; claim: string; source_name: string; source_url: string | null; observed_at: string; source_at: string | null; content_hash: string }
export interface Decision {
  decision_id: string; run_id: string; instrument_id: string; as_of: string; status: string;
  rating: string; confidence: number; thesis: string; risks: string[]; invalidation_conditions: string[];
  data_quality: string; current_weight: number | null; target_weight: number | null; max_allowed_weight: number | null;
  portfolio_snapshot_id: string | null; policy_checks: Check[]; evidence: Evidence[];
}
interface State { candidate: Decision; current_status: string; events: { event_id: string; from_status: string; to_status: string; actor_type: string; occurred_at: string; reason: string }[] }
const weight = (value: number | null) => value === null ? 'Unavailable' : percent(value);
const valueText = (value: unknown) => value === null || value === undefined ? 'Unavailable' : typeof value === 'object' ? 'Structured value' : String(value);
function safeSourceUrl(value: string | null): string | undefined {
  if (!value) return undefined;
  try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? url.href : undefined; }
  catch { return undefined; }
}

export default function Decisions() {
  const [version, setVersion] = useState(0);
  const list = useResource<Decision[]>('/decisions?limit=200', version);
  const catalog = useResource<Instrument[]>('/instruments?limit=500', 0, instruments);
  const [selected, setSelected] = useState(() => new URLSearchParams(window.location.hash.split('?')[1]).get('decision') ?? '');
  useEffect(() => {
    const update = () => setSelected(new URLSearchParams(window.location.hash.split('?')[1]).get('decision') ?? '');
    window.addEventListener('hashchange', update);
    return () => window.removeEventListener('hashchange', update);
  }, []);
  // A deep link may target older research outside the bounded history page.
  // Never silently substitute the first candidate for a missing/unauthorized ID.
  const currentId = selected || list.data?.[0]?.decision_id;
  return <>
    <div className="section-actions"><p className="muted">Research candidates and human review · No order execution.</p><button onClick={() => setVersion(value => value + 1)}>Refresh decisions</button></div>
    <div className="market-layout"><section className="instrument-list" aria-label="Decision history"><div className="list-heading">Research candidates</div>
      {list.loading ? <p role="status">Loading decisions…</p> : list.error ? <p role="alert" className="danger">{errorMessage(list.error)}</p> : !list.data?.length ? <p className="muted">No decision candidates have been published.</p>
        : <ul>{list.data.map(item => <li key={item.decision_id}><button aria-pressed={currentId === item.decision_id} onClick={() => { setSelected(item.decision_id); window.history.replaceState(null, '', `#/decisions?decision=${encodeURIComponent(item.decision_id)}`); }}>
          <span className="instrument-row"><strong>{catalog.data?.find(asset => asset.instrument_id === item.instrument_id)?.canonical_symbol ?? 'Instrument'}</strong><span>{item.rating}</span></span>
          <span className="instrument-name">{timestamp(item.as_of)}</span><span className="caption">Original state: {item.status}</span>
        </button></li>)}</ul>}
    </section>{currentId ? <DecisionDetail key={currentId} id={currentId} version={version} /> : <section className="empty-state"><h2>Select a candidate</h2><p>Evidence, risk checks and the current review state appear here. A research rating is not an approval.</p></section>}</div>
  </>;
}

function DecisionDetail({ id, version }: { id: string; version: number }) {
  const [tick, setTick] = useState(0);
  const state = useResource<State>(`/decisions/${encodeURIComponent(id)}/state`, version + tick);
  const candidate = state.data?.candidate;
  const run = useResource<Run>(candidate ? `/runs/${encodeURIComponent(candidate.run_id)}` : null, version + tick);
  const [action, setAction] = useState<'approve' | 'reject' | null>(null);
  if (state.loading) return <p role="status">Loading decision state…</p>;
  if (state.error || !candidate || !state.data) return <p role="alert" className="danger">{errorMessage(state.error)}</p>;
  const current = state.data.current_status;
  const policies = new Set(candidate.policy_checks.map(check => `${check.policy_id}:${check.policy_version}`));
  const canApprove = current === 'ready_for_approval' && candidate.data_quality === 'OK' && run.data?.status === 'succeeded'
    && candidate.policy_checks.length > 0 && policies.size === 1 && candidate.policy_checks.every(check => !check.blocking || check.result === 'PASS');
  return <section className="instrument-detail" aria-label="Decision details">
    <h2>{candidate.rating} <span className="muted">· Research rating</span></h2>
    <p className="notice">Current state: <strong>{current}</strong> · Original research state: {candidate.status}</p>
    <p className="muted">As of {timestamp(candidate.as_of)} · Data quality: {candidate.data_quality} · Model confidence (uncalibrated): {percent(candidate.confidence)}</p>
    <h3>Thesis</h3><p className="narrative">{candidate.thesis}</p>
    <div className="review-columns"><section><h3>Risks</h3><ul>{candidate.risks.map((text, i) => <li key={i}>{text}</li>)}</ul></section><section><h3>Invalidation conditions</h3><ul>{candidate.invalidation_conditions.map((text, i) => <li key={i}>{text}</li>)}</ul></section></div>
    <div className="metrics"><div><span>Current weight</span><strong>{weight(candidate.current_weight)}</strong></div><div><span>Owner target</span><strong>{weight(candidate.target_weight)}</strong></div><div><span>Maximum allowed</span><strong>{weight(candidate.max_allowed_weight)}</strong></div></div>
    <h3>Deterministic risk checks</h3>
    {!candidate.policy_checks.length ? <p className="warning">No risk checks. Approval is unavailable.</p> : <div className="table-scroll" role="region" aria-label="Policy checks" tabIndex={0}><table><thead><tr><th>Check</th><th>Result</th><th>Observed</th><th>Limit</th><th>Reason</th></tr></thead><tbody>{candidate.policy_checks.map(check => <tr key={check.check_id}><th scope="row">{check.check_id}<small>{check.blocking ? 'Blocking' : 'Informational'}</small></th><td className={check.result === 'PASS' ? '' : 'warning'}>{check.result}</td><td>{valueText(check.observed_value)}</td><td>{valueText(check.limit_value)}</td><td className="wrap-cell">{check.reason}</td></tr>)}</tbody></table></div>}
    <h3>Evidence</h3>{!candidate.evidence.length ? <p className="warning">No cited evidence.</p> : candidate.evidence.map(item => <details className="provenance" key={item.evidence_id}><summary>{item.source_name} · {item.claim}</summary><p>Source: {timestamp(item.source_at)} · Observed: {timestamp(item.observed_at)}</p><p className="mono">Snapshot {item.snapshot_id}</p><p className="mono">{item.content_hash}</p>{safeSourceUrl(item.source_url) ? <a href={safeSourceUrl(item.source_url)} target="_blank" rel="noopener noreferrer">Open external source</a> : null}</details>)}
    <h3>Owner review</h3><p className="muted">This records a decision; it does not place an order. The backend revalidates run, policy and evidence on approval.</p>
    {run.error ? <p className="warning">Run status unavailable. Approval remains disabled.</p> : <p>Source run: {run.data?.status ?? 'Loading…'}</p>}
    {!canApprove && ['review', 'ready_for_approval'].includes(current) ? <p className="warning">Approval is unavailable until the candidate is ready, its run succeeds and blocking checks pass.</p> : null}
    <div className="section-actions"><button className="primary" disabled={!canApprove} onClick={() => setAction('approve')}>Approve decision</button><button disabled={!['review', 'ready_for_approval'].includes(current)} onClick={() => setAction('reject')}>Reject decision</button></div>
    <h3>Audit timeline</h3>{!state.data.events.length ? <p className="muted">No owner lifecycle actions yet.</p> : <ol className="event-list">{state.data.events.map(event => <li key={event.event_id}><strong>{event.from_status} → {event.to_status}</strong><time>{timestamp(event.occurred_at)} · {event.actor_type}</time><p>{event.reason}</p></li>)}</ol>}
    {action ? <ReviewDialog action={action} state={state.data} onClose={() => setAction(null)} onSaved={() => { setAction(null); setTick(value => value + 1); }} /> : null}
  </section>;
}

function ReviewDialog({ action, state, onClose, onSaved }: { action: 'approve' | 'reject'; state: State; onClose: () => void; onSaved: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [reason, setReason] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const requestKey = useRef<{ reason: string; id: string } | null>(null);
  useEffect(() => { const node = dialog.current; node?.showModal(); return () => node?.close(); }, []);
  async function confirm() {
    if (!reason.trim() || pending) return;
    if (requestKey.current?.reason !== reason.trim()) requestKey.current = { reason: reason.trim(), id: crypto.randomUUID() };
    const policy = state.candidate.policy_checks[0];
    setPending(true); setError('');
    try {
      await mutate(`/decisions/${encodeURIComponent(state.candidate.decision_id)}/transitions`, {
        action, event_id: requestKey.current!.id, expected_status: state.current_status, reason: reason.trim(),
        ...(action === 'approve' ? { policy_id: policy.policy_id, policy_version: policy.policy_version } : {}),
      });
      onSaved();
    } catch (cause) { setError(errorMessage(cause)); }
    finally { setPending(false); }
  }
  return <dialog ref={dialog} onCancel={event => { event.preventDefault(); if (!pending) onClose(); }} aria-labelledby="review-title">
    <h2 id="review-title">Confirm {action === 'approve' ? 'approval' : 'rejection'}</h2><p className="mono">{state.candidate.decision_id}</p><p>Current state: {state.current_status}</p><p>This records a decision; it does not place an order.</p>
    <label>Reason<textarea value={reason} onChange={event => setReason(event.target.value)} maxLength={2000} disabled={pending} autoFocus /></label>
    {error ? <p role="alert" className="notice danger">{error} No successful transition has been confirmed. Close and refresh if the record changed.</p> : null}
    <div className="section-actions"><button className="primary" disabled={pending || !reason.trim()} onClick={confirm}>{pending ? 'Submitting…' : `Confirm ${action}`}</button><button disabled={pending} onClick={onClose}>Cancel</button></div>
  </dialog>;
}
