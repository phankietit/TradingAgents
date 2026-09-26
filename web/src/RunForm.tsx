import { useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { errorMessage, mutate } from './api';
import { timestamp, useResource } from './data';
import type { Instrument, Snapshot } from './data';

export interface Run {
  run_id: string; instrument_id: string; analysis_as_of: string; status: string; created_at: string;
  selected_analysts: string[]; error_code: string | null; snapshot_ids: string[];
}
interface Profile { name: string; allowed_analysts: string[]; investable: boolean }
interface Source { snapshot: Snapshot; metadata_eligible: boolean; ineligibility_reasons: string[] }

export default function RunForm({ catalog, initialInstrument, onClose, onCreated }: {
  catalog: Instrument[]; initialInstrument?: string; onClose: () => void; onCreated: (run: Run) => void;
}) {
  const [instrumentId, setInstrumentId] = useState(initialInstrument ?? catalog[0]?.instrument_id ?? '');
  const [asOf, setAsOf] = useState(new Date().toISOString());
  const [maxAge, setMaxAge] = useState('604800');
  const [sources, setSources] = useState<Record<string, string[]>>({});
  const [confirmed, setConfirmed] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const submission = useRef<{ body: string; key: string } | null>(null);
  const profile = useResource<Profile>(instrumentId ? `/instruments/${encodeURIComponent(instrumentId)}/analysis-profile` : null);
  const dateValid = /(?:Z|[+-]\d\d:\d\d)$/.test(asOf) && Number.isFinite(Date.parse(asOf)) && Date.parse(asOf) <= Date.now();
  const ageValid = /^\d+$/.test(maxAge) && Number(maxAge) <= 315360000;
  const discovery = useResource<Source[]>(instrumentId && dateValid && ageValid ? `/instruments/${encodeURIComponent(instrumentId)}/snapshots?${new URLSearchParams({ analysis_as_of: asOf, max_age_seconds: maxAge, limit: '200' })}` : null);
  const selectedRoles = (profile.data?.allowed_analysts ?? []).filter(role => sources[role]?.length);
  const eligible = new Set(discovery.data?.filter(item => item.metadata_eligible).map(item => item.snapshot.snapshot_id));
  const ready = !pending && confirmed && selectedRoles.length > 0 && !profile.loading && !discovery.loading && !discovery.error
    && dateValid && ageValid && selectedRoles.every(role => sources[role].every(id => eligible.has(id)));
  function toggle(role: string, id: string) {
    setSources(previous => ({ ...previous, [role]: previous[role]?.includes(id) ? previous[role].filter(value => value !== id) : [...(previous[role] ?? []), id].slice(0, 16) }));
    setConfirmed(false);
  }
  async function submit(event: FormEvent) {
    event.preventDefault(); if (!ready) return;
    const payload = { instrument_id: instrumentId, analysis_as_of: asOf, selected_analysts: selectedRoles,
      decision_inputs: { snapshots_by_analyst: Object.fromEntries(selectedRoles.map(role => [role, sources[role]])),
        source_max_age_seconds: Object.fromEntries(selectedRoles.map(role => [role, Number(maxAge)])) } };
    const body = JSON.stringify(payload);
    if (submission.current?.body !== body) submission.current = { body, key: crypto.randomUUID() };
    setPending(true); setError('');
    try {
      const result = await mutate<{ run: Run }>('/runs', payload, 'POST', { 'Idempotency-Key': submission.current!.key });
      onCreated(result.run);
    } catch (cause) { setError(errorMessage(cause)); }
    finally { setPending(false); }
  }
  return <form className="analysis-form" onSubmit={submit} aria-label="New analysis" aria-busy={pending}>
    <h2>Configure analysis</h2>
    <p className="muted">Choose evidence for each analyst. The server verifies content and freshness again before queuing. This research-only form does not submit a portfolio weight.</p>
    <fieldset disabled={pending}><div className="form-grid">
      <label>Instrument<select value={instrumentId} onChange={event => { setInstrumentId(event.target.value); setSources({}); setConfirmed(false); }}>{catalog.map(item => <option key={item.instrument_id} value={item.instrument_id}>{item.canonical_symbol} — {item.display_name}</option>)}</select></label>
      <label>Analysis as of (ISO with timezone)<input value={asOf} onChange={event => { setAsOf(event.target.value); setConfirmed(false); }} required /></label>
      <label>Maximum source age (seconds)<input inputMode="numeric" value={maxAge} onChange={event => { setMaxAge(event.target.value); setConfirmed(false); }} required /></label>
    </div>
    {!dateValid ? <p className="warning">Enter an ISO timestamp with timezone, not in the future.</p> : null}
    {!ageValid ? <p className="warning">Source age must be an integer from 0 to 315360000.</p> : null}
    {profile.loading || discovery.loading ? <p role="status">Checking analysis profile and saved sources…</p> : null}
    {profile.error || discovery.error ? <p role="alert" className="danger">{errorMessage(profile.error || discovery.error)}</p> : null}
    {profile.data && !profile.data.investable ? <p className="notice warning">Reference-only research. This instrument cannot become an investable position.</p> : null}
    {profile.data?.allowed_analysts.map(role => <fieldset key={role} className="source-role"><legend>{role} analyst</legend>
      {!discovery.data?.length ? <p className="muted">No saved sources available for this instrument.</p> : discovery.data.map(item => <label className="source-option" key={item.snapshot.snapshot_id}>
        <input type="checkbox" disabled={!item.metadata_eligible || !sources[role]?.includes(item.snapshot.snapshot_id) && sources[role]?.length >= 16}
          checked={sources[role]?.includes(item.snapshot.snapshot_id) ?? false} onChange={() => toggle(role, item.snapshot.snapshot_id)} />
        <span>{item.snapshot.dataset} · {item.snapshot.vendor}<small>{timestamp(item.snapshot.source_end)} · {item.snapshot.quality_status} · {item.metadata_eligible ? 'Metadata eligible; content check pending' : item.ineligibility_reasons.join(', ')}</small></span>
      </label>)}
    </fieldset>)}
    {discovery.data?.length === 200 ? <p className="warning">Only the latest 200 source manifests are shown.</p> : null}
    <label className="source-option"><input type="checkbox" checked={confirmed} onChange={event => setConfirmed(event.target.checked)} /><span>I authorize this analysis run. The configured worker may call paid models; results require human review.</span></label>
    {error ? <p role="alert" className="notice danger">{error} Retrying unchanged inputs reuses the same request key.</p> : null}
    <div className="section-actions"><button className="primary" disabled={!ready}>{pending ? 'Submitting…' : 'Queue analysis'}</button><button type="button" onClick={onClose}>Close configuration</button></div>
    </fieldset>
  </form>;
}
