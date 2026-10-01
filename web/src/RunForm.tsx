import { t, useLocale } from './i18n';
import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { errorMessage, mutate } from './api';
import { timestamp, useResource } from './data';
import type { Instrument, Snapshot } from './data';
import type { Policy, PortfolioSnapshot } from './Portfolio';
import ResearchSetup from './ResearchSetup';
import { portfolioSnapshots, policyHistory } from './portfolioData';
import { datasetLabel, researchLabel } from './researchLabels';
import { preparePrices } from './preparePrices';
import type { Prepared, PreparationProgress } from './preparePrices';

export interface Run {
  run_id: string; instrument_id: string; analysis_as_of: string; status: string; created_at: string;
  selected_analysts: string[]; error_code: string | null; snapshot_ids: string[];
  report_language?: 'en' | 'vi' | 'en-vi' | null;
}
interface Profile { name: string; allowed_analysts: string[]; investable: boolean }
interface Source { snapshot: Snapshot; metadata_eligible: boolean; ineligibility_reasons: string[]; supported_analysts: string[] }
const preparationMessages: Record<string, string> = {
  unsupported: 'Automatic preparation is not available for this instrument. Futures references require contract and roll data; no substitute is used.',
  invalid: 'The data failed validation. Nothing was selected. Please retry later or check the source.',
  no_data: 'Yahoo returned no price history. No analysis was started.',
  stale: 'The latest completed session is missing. Please retry after the source updates.',
  coverage_gap: 'Price history has missing sessions. Analysis remains blocked until coverage is complete.',
  rate_limited: 'Yahoo is limiting requests. Please try again later.',
  cooldown: 'The local service is spacing out download requests. Please try again later.',
  unavailable: 'The price source is unavailable or timed out. Please retry later; no AI call was made.',
  busy: 'Another data request is in progress. Please try again shortly.',
};

export default function RunForm({ catalog, initialInstrument, onClose, onCreated }: {
  catalog: Instrument[]; initialInstrument?: string; onClose: () => void; onCreated: (run: Run) => void;
}) {
  useLocale();
  const [instrumentId, setInstrumentId] = useState(initialInstrument ?? catalog[0]?.instrument_id ?? '');
  const [asOf, setAsOf] = useState(new Date().toISOString());
  const [reportLanguage, setReportLanguage] = useState<'en' | 'vi' | 'en-vi'>('en-vi');
  const [maxAge, setMaxAge] = useState('604800');
  const [sources, setSources] = useState<Record<string, string[]>>({});
  const [riskEnabled, setRiskEnabled] = useState(false);
  const [portfolioId, setPortfolioId] = useState('');
  const [policyKey, setPolicyKey] = useState('');
  const [target, setTarget] = useState('');
  const [riskSources, setRiskSources] = useState<Record<string, string>>({});
  const portfolios = useResource<PortfolioSnapshot[]>('/portfolios?limit=200', 0, portfolioSnapshots);
  const policies = useResource<Policy[]>('/policies?limit=200', 0, policyHistory);
  const portfolio = portfolios.data?.find(item => item.portfolio_id === portfolioId);
  const asset = catalog.find(item => item.instrument_id === instrumentId);
  const policy = policies.data?.find(item => `${item.policy_id}:${item.policy_version}` === policyKey && item.asset_class === asset?.asset_class && Date.parse(item.effective_at) <= Date.parse(asOf));
  const [confirmed, setConfirmed] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [preparing, setPreparing] = useState(false);
  const [newsPending, setNewsPending] = useState(false);
  const [newsNote, setNewsNote] = useState('');
  const [preparationProgress, setPreparationProgress] = useState<PreparationProgress | null>(null);
  const preparationController = useRef<AbortController | null>(null);
  const newsController = useRef<AbortController | null>(null);
  useEffect(() => () => { preparationController.current?.abort(); newsController.current?.abort(); }, []);
  const [preparationNote, setPreparationNote] = useState('');
  const [preparationExhausted, setPreparationExhausted] = useState(false);
  const [dataVersion, setDataVersion] = useState(0);
  const submission = useRef<{ body: string; key: string } | null>(null);
  const profile = useResource<Profile>(instrumentId ? `/instruments/${encodeURIComponent(instrumentId)}/analysis-profile` : null);
  const dateValid = /(?:Z|[+-]\d\d:\d\d)$/.test(asOf) && Number.isFinite(Date.parse(asOf)) && Date.parse(asOf) <= Date.now();
  const ageValid = /^\d+$/.test(maxAge) && Number(maxAge) <= 315360000;
  const discovery = useResource<Source[]>(instrumentId && dateValid && ageValid ? `/instruments/${encodeURIComponent(instrumentId)}/snapshots?${new URLSearchParams({ analysis_as_of: asOf, max_age_seconds: maxAge, limit: '200' })}` : null, dataVersion);
  const selectedRoles = (profile.data?.allowed_analysts ?? []).filter(role => sources[role]?.length);
  const eligible = new Set(discovery.data?.filter(item => item.metadata_eligible).map(item => item.snapshot.snapshot_id));
  const riskReady = !riskEnabled || profile.data?.investable && portfolio && policy && portfolio.as_of === asOf
    && target.trim() !== '' && Number.isFinite(Number(target)) && Number(target) >= 0 && Number(target) <= 1;
  const correlationInstruments = riskEnabled && portfolio && Number(target) > 0
    && portfolio.positions.some(item => Number(item.weight) > 0 && item.instrument_id !== instrumentId)
    ? Array.from(new Set([instrumentId, ...portfolio.positions.filter(item => Number(item.weight) > 0).map(item => item.instrument_id)])) : [];
  const ready = !pending && !preparing && !newsPending && confirmed && selectedRoles.length > 0 && !profile.loading && !discovery.loading && !discovery.error
    && dateValid && ageValid && riskReady && selectedRoles.every(role => sources[role].every(id => eligible.has(id)
      && discovery.data?.find(item => item.snapshot.snapshot_id === id)?.supported_analysts.includes(role)));
  function toggle(role: string, id: string) {
    setSources(previous => ({ ...previous, [role]: previous[role]?.includes(id) ? previous[role].filter(value => value !== id) : [...(previous[role] ?? []), id].slice(0, 16) }));
    setConfirmed(false);
  }
  async function prepare() {
    if (preparationController.current || preparing || newsPending || pending || riskEnabled) return;
    const controller = new AbortController();
    preparationController.current = controller;
    setPreparing(true); setPreparationNote(''); setPreparationExhausted(false); setConfirmed(false); setError('');
    try {
      const result = await preparePrices(instrumentId, controller.signal, setPreparationProgress);
      if (result.status !== 'ready') {
        setPreparationExhausted(result.checks === 3);
        setPreparationNote(preparationMessages[result.last_failure ?? result.status] ?? preparationMessages.unavailable);
        return;
      }
      if (!result.snapshot?.snapshot_id || !Number.isFinite(Date.parse(result.analysis_as_of))) {
        setPreparationNote(preparationMessages.invalid); return;
      }
      setAsOf(result.analysis_as_of);
      setSources(previous => ({ ...previous, market: [result.snapshot!.snapshot_id] }));
      setDataVersion(value => value + 1);
      setPreparationNote(result.reused ? 'Saved prices are current and verified. Review the sources, then authorize AI analysis.'
        : 'Prices are ready. Research time has been updated to now. Review the sources, then authorize AI analysis.');
    } catch (cause) { setPreparationNote(controller.signal.aborted ? 'Automatic retries stopped. A download already received by the server may still finish; no AI analysis was submitted.' : errorMessage(cause)); }
    finally { preparationController.current = null; setPreparationProgress(null); setPreparing(false); }
  }
  async function prepareNews() {
    if (preparing || newsPending || pending || riskEnabled || !profile.data?.allowed_analysts.includes('news')) return;
    const controller = new AbortController();
    newsController.current = controller;
    setNewsPending(true); setNewsNote(''); setConfirmed(false); setError('');
    try {
      const result = await mutate<Prepared>(
        `/instruments/${encodeURIComponent(instrumentId)}/prepare-news`,
        undefined, 'POST', {}, AbortSignal.any([controller.signal, AbortSignal.timeout(60_000)]),
      );
      if (result.status !== 'ready' || !result.snapshot?.snapshot_id || !Number.isFinite(Date.parse(result.analysis_as_of))) {
        const message: Record<string, string> = {
          no_data: 'Yahoo has no recent headlines for this instrument. News research was not selected.',
          coverage_gap: 'Yahoo has no headlines inside the requested recent window. News research was not selected.',
          unavailable: 'Recent headlines are unavailable. The existing price source is unchanged.',
          invalid: 'The news feed failed validation. It was not selected.',
          unsupported: 'Automatic headlines are not available for this reference instrument.',
          busy: 'Another data request is in progress. Please try again shortly.',
          cooldown: 'Please wait one minute before checking headlines again.',
        };
        setNewsNote(message[result.status] ?? 'Recent headlines could not be prepared. No AI analysis was started.');
        return;
      }
      setAsOf(result.analysis_as_of);
      setSources(previous => ({ ...previous, news: [result.snapshot!.snapshot_id] }));
      setDataVersion(value => value + 1);
      setNewsNote(result.reused
        ? 'Saved recent headlines are still eligible. Review coverage before authorizing AI.'
        : 'Recent headlines are ready. This feed is not a complete record of all news. Review coverage before authorizing AI.');
    } catch (cause) { setNewsNote(errorMessage(cause)); }
    finally { newsController.current = null; setNewsPending(false); }
  }
  async function submit(event: FormEvent) {
    event.preventDefault(); if (!ready) return;
    const payload = { instrument_id: instrumentId, analysis_as_of: asOf, selected_analysts: selectedRoles, report_language: reportLanguage,
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
  return <form className="analysis-form" onSubmit={submit} aria-label={t("New analysis")} aria-busy={pending || preparing || newsPending}>
    <h2>{t("Configure analysis")}</h2>
    {preparing && preparationProgress ? <section className="notice" aria-label={t('Data preparation progress')}>
      <p role="status">{t('Checking market data')} · {t('Attempt')} {preparationProgress.attempt}/3</p>
      <progress max={3} value={preparationProgress.waiting ? preparationProgress.attempt : preparationProgress.attempt - 1} aria-label={t('Completed checks')} />
      {preparationProgress.waiting ? <p>{t(preparationProgress.reason === 'cooldown' ? 'Waiting for the local download cooldown.' : preparationProgress.reason === 'rate_limited' ? 'Yahoo is limiting requests.' : 'Data is not ready yet. Retrying automatically.')} {t('Next check in')} {preparationProgress.remaining} {t('seconds')}.</p> : <p>{t('Downloading and checking prices…')}</p>}
      <button type="button" onClick={() => preparationController.current?.abort()}>{t('Stop automatic retries')}</button>
    </section> : null}
    <p className="muted">{t('Build a research brief from verified market evidence. Review the coverage before starting AI analysis.')}</p>
    <label>{t('Report language')}<select value={reportLanguage} disabled={pending || preparing} onChange={event => {
      setReportLanguage(event.target.value as 'en' | 'vi' | 'en-vi'); setConfirmed(false);
    }}>
      <option value="en-vi">{t('English + Vietnamese')}</option><option value="vi">{t('Vietnamese')}</option><option value="en">{t('English')}</option>
    </select></label>
    <p className="muted">{t('Choose the language for new research. Bilingual reports may use more output tokens. Changing the interface language does not translate saved reports.')}</p>
    <p className="muted">{t("Choose the instrument, research date and supporting sources. You can also review the impact on your portfolio using an allocation you specify.")}</p>
    <fieldset disabled={pending || preparing || newsPending}><div className="form-grid">
      <label>{t("Instrument")}<select value={instrumentId} onChange={event => { setInstrumentId(event.target.value); setPreparationNote(''); setNewsNote(''); setSources({}); setRiskEnabled(false); setPolicyKey(''); setRiskSources({}); setConfirmed(false); }}>{catalog.map(item => <option key={item.instrument_id} value={item.instrument_id}>{item.canonical_symbol} — {item.display_name}</option>)}</select></label>
      <label>{t("Research date & time (UTC)")}<input type="datetime-local" step="0.001" value={Number.isFinite(Date.parse(asOf)) ? new Date(asOf).toISOString().slice(0, -1) : ''} disabled={riskEnabled} onChange={event => { setAsOf(event.target.value ? `${event.target.value}Z` : ''); setConfirmed(false); }} required /></label>
    </div>
    <section className="notice" aria-label={t('Prepare market data')}>
      <h3>{t('1. Prepare market data')}</h3>
      <p>{t('Download five years of completed daily prices, matching the original research engine, or reuse verified history. Yahoo needs no API key. This step does not use AI tokens.')}</p>
      <p className="muted">{t('This prepares price and trend research only. News, fundamentals, sentiment and macro evidence are not downloaded by this step.')}</p>
      <p className="muted">{t('New data is for research now, not a historical replay. Preparing data updates the research time; old reports remain unchanged.')}</p>
      <button type="button" disabled={riskEnabled || !instrumentId || newsPending} onClick={() => void prepare()}>{preparing ? t('Downloading and checking prices…') : t('Prepare latest prices')}</button>
      {riskEnabled ? <p>{t('Turn off portfolio evaluation to prepare current prices. Portfolio research must keep its original valuation time.')}</p> : null}
      {preparationNote ? <p role={preparationExhausted ? 'alert' : 'status'}>{preparationExhausted ? `${t('Data is still incomplete after three checks.')} ` : ''}{t(preparationNote)}</p> : null}
      {profile.data?.allowed_analysts.includes('news') ? <div className="news-supplement">
        <h4>{t('Current headlines · optional')}</h4>
        <p>{t('Collect recent Yahoo headlines as a separate source. Coverage is not exhaustive or historical. This step uses no AI tokens.')}</p>
        <button type="button" disabled={riskEnabled || !instrumentId || preparing || newsPending} onClick={() => void prepareNews()}>{newsPending ? t('Checking headlines…') : t('Add recent headlines')}</button>
        {newsNote ? <p role="status">{t(newsNote)}</p> : null}
      </div> : null}
    </section>
    <p className="muted">{t("All research times use UTC. Sources must be available by the selected time and pass content checks before research begins.")}</p>
    <details><summary>{t("Advanced data settings")}</summary>
      <label>{t("Maximum source age (seconds)")}<input inputMode="numeric" value={maxAge} onChange={event => { setMaxAge(event.target.value); setConfirmed(false); }} required /></label>
      <p className="muted">{t("The existing limit is measured against the research time. Changing it does not override source quality or portfolio policy checks.")}</p>
      <p className="mono">{t("Exact research timestamp:")} {asOf || 'Not selected'}</p>
    </details>
    {!dateValid ? <p className="warning">{t("Select a valid research date and time, not in the future.")}</p> : null}
    {!ageValid ? <p className="warning">{t("Check Advanced data settings: source age must be a whole number from 0 to 315360000 seconds.")}</p> : null}
    {profile.loading || discovery.loading ? <p role="status">{t("Checking analysis profile and saved sources…")}</p> : null}
    {profile.error || discovery.error ? <p role="alert" className="danger">{t(errorMessage(profile.error || discovery.error))}</p> : null}
    {profile.data && !profile.data.investable ? <p className="notice warning">{t("Reference-only research. This instrument cannot become an investable position.")}</p> : null}
    <label className="source-option"><input type="checkbox" checked={riskEnabled} disabled={!profile.data?.investable}
      onChange={event => { setRiskEnabled(event.target.checked); setConfirmed(false); }} /><span>{t("Evaluate against my portfolio and an existing risk policy")}</span></label>
    {riskEnabled ? <section className="risk-inputs"><p className="notice">{t("The portfolio snapshot pins the analysis timestamp. These inputs request deterministic evaluation; they cannot waive a policy failure or create an order.")}</p>
      {portfolios.error || policies.error ? <p role="alert" className="danger">{t(errorMessage(portfolios.error || policies.error))}</p> : null}
      <div className="form-grid"><label>{t("Portfolio snapshot")}<select value={portfolioId} onChange={event => {
        setPortfolioId(event.target.value); const selected = portfolios.data?.find(item => item.portfolio_id === event.target.value);
        if (selected) setAsOf(selected.as_of); setRiskSources({}); setSources({}); setPolicyKey(''); setConfirmed(false);
      }} required><option value="">{t("Choose a valued snapshot")}</option>{portfolios.data?.map((item,index) => <option key={item.portfolio_id} value={item.portfolio_id}>{item.base_currency} · {timestamp(item.as_of)}  {t("· Record")} {index+1}</option>)}</select></label>
      <label>{t("Risk policy version")}<select value={policyKey} onChange={event => { setPolicyKey(event.target.value); setRiskSources({}); setConfirmed(false); }} required><option value="">{t("Choose an existing policy")}</option>{policies.data?.filter(item => item.asset_class === asset?.asset_class && Date.parse(item.effective_at) <= Date.parse(asOf)).map(item => <option key={`${item.policy_id}:${item.policy_version}`} value={`${item.policy_id}:${item.policy_version}`}>{item.name}  {t("· v")}{item.policy_version}</option>)}</select></label>
      <label>{t("Owner target weight (0–1)")}<input type="number" min="0" max="1" step="any" value={target} onChange={event => { setTarget(event.target.value); setConfirmed(false); }} required /></label></div>
      <p className="muted">{t("Enter the portfolio allocation you want to evaluate: 0.20 means 20%. This is your input, not a model recommendation or an order.")}</p>
      {!portfolios.data?.length || !policies.data?.length ? <p className="warning">{t("A valued owner portfolio and a governed policy are required. This form does not create either.")}</p> : null}
      {correlationInstruments.length ? <><h3>{t("Correlation evidence")}</h3><p className="muted">{t("Select daily price snapshots for the proposal and other holdings. Backend validates window alignment, currency, integrity and policy freshness. Missing coverage remains blocking REVIEW.")}</p>
        {correlationInstruments.map(id => <RiskSource key={`${portfolioId}:${policyKey}:${id}`} instrumentId={id} label={catalog.find(item => item.instrument_id === id)?.canonical_symbol ?? id}
          asOf={asOf} maxAge={Number(policy?.parameters.correlation_max_age_seconds ?? 0)} selected={riskSources[id] ?? ''}
          onChange={value => { setRiskSources(previous => ({ ...previous, [id]: value })); setConfirmed(false); }} />)}</> : null}
    </section> : null}
    <section className="coverage-overview"><h3>{t('Research coverage')}</h3><div className="coverage-grid">{profile.data?.allowed_analysts.map(role => <div key={role}><span>{researchLabel(role)}</span><strong className={selectedRoles.includes(role) ? 'coverage-included' : 'muted'}>{selectedRoles.includes(role) ? t('Included') : t('Not included')}</strong></div>)}</div>
      {profile.data && selectedRoles.length < profile.data.allowed_analysts.length ? <p className="muted caption">{t('This is a limited-scope report. Missing research areas will remain unavailable, not filled in by AI.')}</p> : null}
    </section>
    <details className="source-inspector"><summary>{t('Inspect or change evidence sources')}</summary>
    {profile.data?.allowed_analysts.map(role => <fieldset key={role} className="source-role"><legend>{researchLabel(role)}</legend>
      {!discovery.data?.some(item => item.supported_analysts.includes(role)) ? <p className="muted">{t("No suitable saved sources for this research area. It will not be included.")}</p> : discovery.data.filter(item => item.supported_analysts.includes(role)).map(item => <label className="source-option" key={item.snapshot.snapshot_id}>
        <input type="checkbox" disabled={!item.metadata_eligible || !item.supported_analysts.includes(role) || !sources[role]?.includes(item.snapshot.snapshot_id) && sources[role]?.length >= 16}
          checked={sources[role]?.includes(item.snapshot.snapshot_id) ?? false} onChange={() => toggle(role, item.snapshot.snapshot_id)} />
        <span>{datasetLabel(item.snapshot.dataset)} · {item.snapshot.vendor}<small>{timestamp(item.snapshot.source_end)}  {t("· Quality:")} {item.snapshot.quality_status} · {item.metadata_eligible ? t("Available to select; verified before research") : item.ineligibility_reasons.join(', ')}</small>
          {item.snapshot.metadata?.freshness === 'delayed' ? <small className="warning">{t('Source publication is delayed by one daily candle. Research uses completed prices only through:')} {timestamp(item.snapshot.source_end)} (UTC). {t('This is not a current-market assessment. No missing candle is filled.')}</small> : null}
        </span>
      </label>)}
    </fieldset>)}
    {discovery.data?.length === 200 ? <p className="warning">{t("Only the latest 200 source manifests are shown.")}</p> : null}
    </details>
    <h3>{t('2. Review sources and authorize AI')}</h3>
    {!selectedRoles.length ? <p className="warning">{t('To continue, prepare latest prices above or select an eligible saved source. No AI analysis has been submitted.')}</p> : null}
    {selectedRoles.some(role => sources[role].some(id => !eligible.has(id))) ? <p className="warning">{t('A selected source is not eligible for this research time. Prepare current prices or change the selection.')}</p> : null}
    {!riskReady ? <p className="warning">{t('Complete the portfolio, policy and target allocation inputs, or turn off portfolio evaluation.')}</p> : null}
    <label className="source-option"><input type="checkbox" checked={confirmed} onChange={event => setConfirmed(event.target.checked)} /><span>{t("I authorize this analysis run. The configured worker may call paid models; results require human review.")}</span></label>
    {!confirmed && selectedRoles.length > 0 ? <p className="muted">{t('One final step: authorize the AI run above to enable submission.')}</p> : null}
    {error ? <p role="alert" className="notice danger">{t(error)}  {t("Retrying unchanged inputs reuses the same request key.")}</p> : null}
    <div className="section-actions"><button className="primary" disabled={!ready}>{pending ? t("Submitting…") : t("Queue analysis")}</button><button type="button" onClick={onClose}>{t("Close configuration")}</button></div>
    <details><summary>{t('Processing setup')}</summary><ResearchSetup /></details>
    </fieldset>
  </form>;
}

function RiskSource({ instrumentId, label, asOf, maxAge, selected, onChange }: { instrumentId: string; label: string; asOf: string; maxAge: number; selected: string; onChange: (value: string) => void }) {
  useLocale();
  const sources = useResource<Source[]>(`/instruments/${encodeURIComponent(instrumentId)}/snapshots?${new URLSearchParams({ analysis_as_of: asOf, max_age_seconds: String(maxAge), limit: '200' })}`);
  return <label>{label}  {t("correlation snapshot")}<select value={selected} onChange={event => onChange(event.target.value)}><option value="">{t("No correlation source selected")}</option>{sources.data?.filter(item => item.supported_analysts.includes('market')).map(item => <option key={item.snapshot.snapshot_id} value={item.snapshot.snapshot_id} disabled={!item.metadata_eligible}>{item.snapshot.dataset} · {timestamp(item.snapshot.source_end)} · {item.metadata_eligible ? t("Metadata eligible") : item.ineligibility_reasons.join(', ')}</option>)}</select>{sources.error ? <span className="danger">{t(errorMessage(sources.error))}</span> : null}</label>;
}
