import { t, useLocale } from './i18n';
import { useEffect, useState } from 'react';
import { ApiError, errorMessage, request } from './api';
import { timestamp } from './data';
import { profileLabel, researchLabel } from './researchLabels';
import ResearchMarkdown from './ResearchMarkdown';
import ResearchChart, { reportHistories, type ReportHistory } from './ResearchChart';

export interface Artifact { artifact_id: string; kind: string; media_type: string; content_hash: string; byte_size: number; created_at: string }
export function artifactList(value: Artifact[]): Artifact[] {
  if (!Array.isArray(value) || value.some(item => !item || typeof item.artifact_id !== 'string'
      || typeof item.kind !== 'string' || typeof item.media_type !== 'string' || typeof item.content_hash !== 'string'
      || !Number.isSafeInteger(item.byte_size) || item.byte_size < 1 || typeof item.created_at !== 'string')) throw new ApiError(502);
  return value;
}
const MAX_PREVIEW_BYTES = 1_000_000;
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
type JsonObject = Record<string, unknown>;
function object(value: unknown): JsonObject {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new ApiError(502);
  return value as JsonObject;
}
function text(value: unknown): string {
  if (typeof value !== 'string') throw new ApiError(502);
  return value;
}
function list(value: unknown): unknown[] {
  if (!Array.isArray(value)) throw new ApiError(502);
  return value;
}
interface Source { id: string; snapshot: string; name: string; hash: string; claim: string; sourceAt: string | null; observedAt: string }
type Preview = { type: 'report'; decisionId: string; profile: string; referenceOnly: boolean; analysts: string[]; attestation: string; narrative: string; structured: unknown; reportLanguage: string | null; histories: ReportHistory[]; localized: { en: string; vi: string } | null; warning: string; issues: string[]; usage: JsonObject | null; sections: {title:string; body:string}[] }
  | { type: 'evidence'; asOf: string; claims: { id: string; claim: string; sources: Source[] }[] };

function parse(value: unknown, artifact: Artifact, runId: string): Preview {
  const data = object(value);
  if (data.run_id !== runId) throw new ApiError(502);
  if (artifact.kind === 'analysis_report') {
    const decisionId = text(data.decision_id);
    if (!uuid.test(decisionId) || typeof data.reference_only !== 'boolean') throw new ApiError(502);
    const localized = data.localized_report ? object(data.localized_report) : null;
    const research = data.research_sections === undefined ? {} : object(data.research_sections);
    const debates = data.debate_sections === undefined ? {} : object(data.debate_sections);
    const sectionNames: Record<string,string> = {market_report:'Market Analyst',sentiment_report:'Sentiment Analyst',news_report:'News Analyst',fundamentals_report:'Fundamentals Analyst',investment_plan:'Research Manager',trader_investment_plan:'Trader',investment_debate_state:'Bull & bear debate',risk_debate_state:'Risk debate'};
    const sections = Object.entries({...research,...debates}).filter(([key]) => Object.hasOwn(sectionNames,key))
      .map(([key,value]) => ({title:sectionNames[key],body:text(value)})).filter(section => section.body.length > 0);
    return { type: 'report', decisionId, profile: text(data.profile), referenceOnly: data.reference_only,
      analysts: list(data.selected_analysts).map(text), attestation: text(data.snapshot_attestation),
      narrative: text(data.narrative), structured: data.structured_narrative,
      reportLanguage: ['en', 'vi', 'en-vi'].includes(String(data.report_language)) ? String(data.report_language) : null,
      histories: reportHistories(data.market_history),
      localized: localized ? { en: text(localized.en), vi: text(localized.vi) } : null,
      warning: data.publication_warning === undefined ? '' : text(data.publication_warning),
      issues: data.validation_issues === undefined ? [] : list(data.validation_issues).map(text),
      usage: data.execution ? object(object(data.execution).usage) : null, sections };
  }
  if (artifact.kind !== 'decision_evidence' || data.graph_id !== artifact.artifact_id) throw new ApiError(502);
  const sources = list(data.evidence).map(value => {
    const row = object(value);
    return { id: text(row.evidence_id), snapshot: text(row.snapshot_id), name: text(row.source_name),
      hash: text(row.content_hash), claim: text(row.claim), sourceAt: row.source_at === null ? null : text(row.source_at), observedAt: text(row.observed_at) };
  });
  if (new Set(sources.map(source => source.id)).size !== sources.length) throw new ApiError(502);
  const claims = list(data.claims).map(value => {
    const row = object(value);
    const claim = text(row.claim);
    const linked = list(row.evidence_ids).map(id => {
      const source = sources.find(source => source.id === id);
      if (!source || source.claim !== claim) throw new ApiError(502);
      return source;
    });
    if (!linked.length) throw new ApiError(502);
    return { id: text(row.claim_id), claim, sources: linked };
  });
  return { type: 'evidence', asOf: text(data.as_of), claims };
}

export default function ArtifactPreview({ artifact, runId, defaultOpen = false, embedded = false }: { artifact: Artifact; runId: string; defaultOpen?: boolean; embedded?: boolean }) {
  useLocale();
  const [open, setOpen] = useState(defaultOpen);
  const supported = artifact.media_type === 'application/json' && ['analysis_report', 'decision_evidence'].includes(artifact.kind)
    && Number.isSafeInteger(artifact.byte_size) && artifact.byte_size > 0 && artifact.byte_size <= MAX_PREVIEW_BYTES;
  return <>
    {supported ? !embedded && <button onClick={() => setOpen(value => !value)} aria-expanded={open}>{open ? t("Close") : t("Inspect")} {t(artifact.kind.replaceAll('_', ' '))}</button>
      : <p className="muted caption">{t("Inline preview unavailable for this format or size; use the integrity-checked download.")}</p>}
    {(open || embedded) && supported ? <PreviewBody key={`${runId}:${artifact.artifact_id}`} artifact={artifact} runId={runId} /> : null}
  </>;
}

function PreviewBody({ artifact, runId }: { artifact: Artifact; runId: string }) {
  const locale = useLocale();
  const [state, setState] = useState<{ data?: Preview; error?: unknown }>({});
  const [section, setSection] = useState('summary');
  useEffect(() => {
    const controller = new AbortController();
    request<unknown>(`/artifacts/${encodeURIComponent(artifact.artifact_id)}`, { signal: controller.signal }, MAX_PREVIEW_BYTES)
      .then(value => parse(value, artifact, runId))
      .then(data => { if (!controller.signal.aborted) setState({ data }); })
      .catch(error => { if (!controller.signal.aborted) setState({ error }); });
    return () => controller.abort();
  }, [artifact, runId]);
  if (state.error) return <p role="alert" className="danger">{t("Preview unavailable.")} {t(errorMessage(state.error))}  {t("No report contents are shown.")}</p>;
  if (!state.data) return <p role="status">{t("Loading saved report…")}</p>;
  const data = state.data;
  const rating = data.type === 'report' && data.structured && typeof data.structured === 'object' && !Array.isArray(data.structured)
    ? (data.structured as JsonObject).rating : null;
  const outlook = typeof rating === 'string' && ['Buy','Overweight','Hold','Underweight','Sell'].includes(rating) && data.type === 'report' && !data.issues.length ? rating : null;
  return <section className="artifact-preview" aria-label={`${t(artifact.kind.replaceAll('_', ' '))} preview`}>
    {data.type === 'report' ? <>
      <header className="report-header"><div><h3>{t('Research brief')}</h3><p className="muted caption">{profileLabel(data.profile)} · {data.analysts.map(researchLabel).join(', ')}</p></div>
        <span className={data.issues.length || !data.structured ? 'warning' : 'coverage-included'}>{t(data.issues.length || !data.structured ? 'Needs validation' : 'For human review')}</span></header>
      {data.referenceOnly ? <p className="warning">{t("Reference only — not investable.")}</p> : null}
      {data.issues.length ? <p className="notice warning">{t('This report has unresolved validation findings. It is available for inspection, not an approved investment conclusion.')}</p> : null}
      <nav className="report-navigation" aria-label={t('Report sections')}>
        {[['summary','Summary'],['prices','Price history'],['research','Research detail'],['audit','Verification']].map(([key,label]) =>
          <button key={key} aria-pressed={section === key} onClick={() => setSection(key)}>{t(label)}</button>)}
      </nav>
      {section === 'prices' ? <section aria-label={t('Price history')}>
        {data.histories.length ? data.histories.map(history => <ResearchChart key={history.snapshot_id} history={history} />) : <p className="muted">{t('No saved price chart in this report.')}</p>}
      </section> : null}
      {section === 'summary' ? <section className="report-reading" aria-label={t('Summary')}>
      {outlook ? <div className="report-outlook"><span>{t('Research outlook')}</span><strong>{t(outlook)}</strong><small>{t('Research assessment, not an instruction to trade.')}</small></div> : null}
      {data.localized && data.warning ? <p className="notice warning">{data.warning}</p> : null}
      {data.issues.includes('structured_output_missing') ? <>
        <p>{t('The model response did not pass the report format checks. The saved market chart remains available; no validated conclusion was published.')}</p>
        <details><summary>{t('Inspect the unvalidated model response')}</summary><ResearchMarkdown text={data.narrative} /></details>
      </> : <ResearchMarkdown text={data.localized?.[locale] ?? data.narrative} language={data.localized ? locale : data.reportLanguage === 'vi' ? 'vi' : data.reportLanguage === 'en' ? 'en' : undefined} />}
      <p className="report-footnote">{t('Saved research, not a live market signal. Review the evidence, limitations and your portfolio before deciding.')}</p>
      <a className="action-link" href={`#/decisions?decision=${encodeURIComponent(data.decisionId)}`}>{t("Review linked decision")}</a>
      </section> : null}
      {section === 'research' ? <section aria-label={t('Research detail')}><p className="muted caption">{t('Intermediate research, not the final conclusion. Conflicting arguments are preserved for review.')}</p>
        {data.sections.map(section => <details key={section.title}><summary>{t(section.title)}</summary><ResearchMarkdown text={section.body} /></details>)}
        {!data.sections.length ? <p className="muted">{t('No intermediate reports were saved.')}</p> : null}
      </section> : null}
      {section === 'audit' ? <section aria-label={t('Verification')}>
      <p className="muted caption">{t("Immutable research artifact · Not current approval state. Text is displayed without executing HTML or external content.")}</p>
      <p>{t("Snapshot attestation:")} {data.attestation}</p>
      <p className="muted caption">{t('Original report · Language requested:')} {t(data.reportLanguage === 'en-vi' ? 'English + Vietnamese' : data.reportLanguage === 'vi' ? 'Vietnamese' : data.reportLanguage === 'en' ? 'English' : 'Legacy / not recorded')}</p>
      <p className="muted caption">{t('Original analysis text is preserved. Language preference guides generation; translation accuracy still requires human review.')}</p>
      <details><summary>{t("Structured research output")}</summary><pre className="safe-text">{JSON.stringify(data.structured ?? null, null, 2)}</pre></details>
      <details><summary>{t('Validation & model usage')}</summary>{data.issues.length ? <ul>{data.issues.map(issue => <li key={issue}>{issue}</li>)}</ul> : <p>{t('No automated finding recorded. Human financial review remains required.')}</p>}
        {data.usage ? <pre className="safe-text">{JSON.stringify(data.usage, null, 2)}</pre> : <p>{t('Token usage was not recorded for this report.')}</p>}
      </details>
      </section> : null}
    </> : <>
      <p>{t("Evidence as of")} {timestamp(data.asOf)}</p>
      {!data.claims.length ? <p className="warning">{t("No material claims are linked. This is not evidence of a valid conclusion.")}</p> : data.claims.map(claim => <details key={claim.id}>
        <summary>{claim.claim}</summary>{claim.sources.map(source => <dl key={source.id}>
          <dt>{t("Source")}</dt><dd>{source.name}</dd><dt>{t("Source time")}</dt><dd>{timestamp(source.sourceAt)}</dd>
          <dt>{t("Observed")}</dt><dd>{timestamp(source.observedAt)}</dd><dt>{t("Snapshot")}</dt><dd className="mono">{source.snapshot}</dd>
          <dt>{t("Content hash")}</dt><dd className="mono">{source.hash}</dd>
        </dl>)}
      </details>)}
    </>}
  </section>;
}
