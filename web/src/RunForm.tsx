import { useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { errorMessage, mutate } from './api';
import { timestamp, useResource } from './data';
import type { Instrument, Snapshot } from './data';
import type { Policy, PortfolioSnapshot } from './Portfolio';

export interface Run {
  run_id: string; instrument_id: string; analysis_as_of: string; status: string; created_at: string;
  selected_analysts: string[]; error_code: string | null; snapshot_ids: string[];
}
interface Profile { name: string; allowed_analysts: string[]; investable: boolean }
interface Source { snapshot: Snapshot; metadata_eligible: boolean; ineligibility_reasons: string[]; supported_analysts: string[] }

export default function RunForm({ catalog, initialInstrument, onClose, onCreated }: {
  catalog: Instrument[]; initialInstrument?: string; onClose: () => void; onCreated: (run: Run) => void;
}) {
  const [instrumentId, setInstrumentId] = useState(initialInstrument ?? catalog[0]?.instrument_id ?? '');
  const [asOf, setAsOf] = useState(new Date().toISOString());
  const [maxAge, setMaxAge] = useState('604800');
  const [sources, setSources] = useState<Record<string, string[]>>({});
  const [riskEnabled, setRiskEnabled] = useState(false);
  const [portfolioId, setPortfolioId] = useState('');
  const [policyKey, setPolicyKey] = useState('');
  const [target, setTarget] = useState('');
  const [riskSources, setRiskSources] = useState<Record<string, string>>({});
  const portfolios = useResource<PortfolioSnapshot[]>('/portfolios?limit=200');
  const policies = useResource<Policy[]>('/policies?limit=200');
  const portfolio = portfolios.data?.find(item => item.portfolio_id === portfolioId);
  const asset = catalog.find(item => item.instrument_id === instrumentId);
  const policy = policies.data?.find(item => `${item.policy_id}:${item.policy_version}` === policyKey && item.asset_class === asset?.asset_class && Date.parse(item.effective_at) <= Date.parse(asOf));
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
  const riskReady = !riskEnabled || profile.data?.investable && portfolio && policy && portfolio.as_of === asOf
    && target.trim() !== '' && Number.isFinite(Number(target)) && Number(target) >= 0 && Number(target) <= 1;
  const correlationInstruments = riskEnabled && portfolio && Number(target) > 0
    && portfolio.positions.some(item => Number(item.weight) > 0 && item.instrument_id !== instrumentId)
    ? Array.from(new Set([instrumentId, ...portfolio.positions.filter(item => Number(item.weight) > 0).map(item => item.instrument_id)])) : [];
  const ready = !pending && confirmed && selectedRoles.length > 0 && !profile.loading && !discovery.loading && !discovery.error
    && dateValid && ageValid && riskReady && selectedRoles.every(role => sources[role].every(id => eligible.has(id)
      && discovery.data?.find(item => item.snapshot.snapshot_id === id)?.supported_analysts.includes(role)));
  function toggle(role: string, id: string) {
    setSources(previous => ({ ...previous, [role]: previous[role]?.includes(id) ? previous[role].filter(value => value !== id) : [...(previous[role] ?? []), id].slice(0, 16) }));
    setConfirmed(false);
  }
  async function submit(event: FormEvent) {
    event.preventDefault(); if (!ready) return;
    const payload = { instrument_id: instrumentId, analysis_as_of: asOf, selected_analysts: selectedRoles,
      decision_inputs: { snapshots_by_analyst: Object.fromEntries(selectedRoles.map(role => [role, sources[role]])),
        source_max_age_seconds: Object.fromEntries(selectedRoles.map(role => [role, Number(maxAge)])),
        ...(riskEnabled && portfolio && policy ? { portfolio_snapshot_id: portfolio.portfolio_id,
          policy_id: policy.policy_id, policy_version: policy.policy_version, requested_target_weight: Number(target),
          risk_snapshot_ids: correlationInstruments.map(id => riskSources[id]).filter(Boolean) } : {}) } };
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
    <p className="muted">Choose evidence for each analyst. The server verifies content and freshness again before queuing. Portfolio evaluation is optional and uses an explicit owner target, never a model-generated weight.</p>
    <fieldset disabled={pending}><div className="form-grid">
      <label>Instrument<select value={instrumentId} onChange={event => { setInstrumentId(event.target.value); setSources({}); setRiskEnabled(false); setPolicyKey(''); setRiskSources({}); setConfirmed(false); }}>{catalog.map(item => <option key={item.instrument_id} value={item.instrument_id}>{item.canonical_symbol} — {item.display_name}</option>)}</select></label>
      <label>Analysis as of (ISO with timezone)<input value={asOf} disabled={riskEnabled} onChange={event => { setAsOf(event.target.value); setConfirmed(false); }} required /></label>
      <label>Maximum source age (seconds)<input inputMode="numeric" value={maxAge} onChange={event => { setMaxAge(event.target.value); setConfirmed(false); }} required /></label>
    </div>
    {!dateValid ? <p className="warning">Enter an ISO timestamp with timezone, not in the future.</p> : null}
    {!ageValid ? <p className="warning">Source age must be an integer from 0 to 315360000.</p> : null}
    {profile.loading || discovery.loading ? <p role="status">Checking analysis profile and saved sources…</p> : null}
    {profile.error || discovery.error ? <p role="alert" className="danger">{errorMessage(profile.error || discovery.error)}</p> : null}
    {profile.data && !profile.data.investable ? <p className="notice warning">Reference-only research. This instrument cannot become an investable position.</p> : null}
    <label className="source-option"><input type="checkbox" checked={riskEnabled} disabled={!profile.data?.investable}
      onChange={event => { setRiskEnabled(event.target.checked); setConfirmed(false); }} /><span>Evaluate against my portfolio and an existing risk policy</span></label>
    {riskEnabled ? <section className="risk-inputs"><p className="notice">The portfolio snapshot pins the analysis timestamp. These inputs request deterministic evaluation; they cannot waive a policy failure or create an order.</p>
      {portfolios.error || policies.error ? <p role="alert" className="danger">{errorMessage(portfolios.error || policies.error)}</p> : null}
      <div className="form-grid"><label>Portfolio snapshot<select value={portfolioId} onChange={event => {
        setPortfolioId(event.target.value); const selected = portfolios.data?.find(item => item.portfolio_id === event.target.value);
        if (selected) setAsOf(selected.as_of); setRiskSources({}); setSources({}); setPolicyKey(''); setConfirmed(false);
      }} required><option value="">Choose a valued snapshot</option>{portfolios.data?.map(item => <option key={item.portfolio_id} value={item.portfolio_id}>{item.base_currency} · {timestamp(item.as_of)} · {item.portfolio_id.slice(0, 8)}</option>)}</select></label>
      <label>Risk policy version<select value={policyKey} onChange={event => { setPolicyKey(event.target.value); setRiskSources({}); setConfirmed(false); }} required><option value="">Choose an existing policy</option>{policies.data?.filter(item => item.asset_class === asset?.asset_class && Date.parse(item.effective_at) <= Date.parse(asOf)).map(item => <option key={`${item.policy_id}:${item.policy_version}`} value={`${item.policy_id}:${item.policy_version}`}>{item.name} · v{item.policy_version}</option>)}</select></label>
      <label>Owner target weight (0–1)<input type="number" min="0" max="1" step="any" value={target} onChange={event => { setTarget(event.target.value); setConfirmed(false); }} required /></label></div>
      {!portfolios.data?.length || !policies.data?.length ? <p className="warning">A valued owner portfolio and a governed policy are required. This form does not create either.</p> : null}
      {correlationInstruments.length ? <><h3>Correlation evidence</h3><p className="muted">Select daily price snapshots for the proposal and other holdings. Backend validates window alignment, currency, integrity and policy freshness. Missing coverage remains blocking REVIEW.</p>
        {correlationInstruments.map(id => <RiskSource key={`${portfolioId}:${policyKey}:${id}`} instrumentId={id} label={catalog.find(item => item.instrument_id === id)?.canonical_symbol ?? id}
          asOf={asOf} maxAge={Number(policy?.parameters.correlation_max_age_seconds ?? 0)} selected={riskSources[id] ?? ''}
          onChange={value => { setRiskSources(previous => ({ ...previous, [id]: value })); setConfirmed(false); }} />)}</> : null}
    </section> : null}
    {profile.data?.allowed_analysts.map(role => <fieldset key={role} className="source-role"><legend>{role} analyst</legend>
      {!discovery.data?.length ? <p className="muted">No saved sources available for this instrument.</p> : discovery.data.map(item => <label className="source-option" key={item.snapshot.snapshot_id}>
        <input type="checkbox" disabled={!item.metadata_eligible || !item.supported_analysts.includes(role) || !sources[role]?.includes(item.snapshot.snapshot_id) && sources[role]?.length >= 16}
          checked={sources[role]?.includes(item.snapshot.snapshot_id) ?? false} onChange={() => toggle(role, item.snapshot.snapshot_id)} />
        <span>{item.snapshot.dataset} · {item.snapshot.vendor}<small>{timestamp(item.snapshot.source_end)} · {item.snapshot.quality_status} · {!item.supported_analysts.includes(role) ? 'Dataset not suitable for this analyst' : item.metadata_eligible ? 'Metadata eligible; content check pending' : item.ineligibility_reasons.join(', ')}</small></span>
      </label>)}
    </fieldset>)}
    {discovery.data?.length === 200 ? <p className="warning">Only the latest 200 source manifests are shown.</p> : null}
    <label className="source-option"><input type="checkbox" checked={confirmed} onChange={event => setConfirmed(event.target.checked)} /><span>I authorize this analysis run. The configured worker may call paid models; results require human review.</span></label>
    {error ? <p role="alert" className="notice danger">{error} Retrying unchanged inputs reuses the same request key.</p> : null}
    <div className="section-actions"><button className="primary" disabled={!ready}>{pending ? 'Submitting…' : 'Queue analysis'}</button><button type="button" onClick={onClose}>Close configuration</button></div>
    </fieldset>
  </form>;
}

function RiskSource({ instrumentId, label, asOf, maxAge, selected, onChange }: { instrumentId: string; label: string; asOf: string; maxAge: number; selected: string; onChange: (value: string) => void }) {
  const sources = useResource<Source[]>(`/instruments/${encodeURIComponent(instrumentId)}/snapshots?${new URLSearchParams({ analysis_as_of: asOf, max_age_seconds: String(maxAge), limit: '200' })}`);
  return <label>{label} correlation snapshot<select value={selected} onChange={event => onChange(event.target.value)}><option value="">No correlation source selected</option>{sources.data?.filter(item => item.supported_analysts.includes('market')).map(item => <option key={item.snapshot.snapshot_id} value={item.snapshot.snapshot_id} disabled={!item.metadata_eligible}>{item.snapshot.dataset} · {timestamp(item.snapshot.source_end)} · {item.metadata_eligible ? 'Metadata eligible' : item.ineligibility_reasons.join(', ')}</option>)}</select>{sources.error ? <span className="danger">{errorMessage(sources.error)}</span> : null}</label>;
}
