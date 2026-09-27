import { t, useLocale } from './i18n';
import { useEffect, useState } from 'react';
import { ApiError, errorMessage, request } from './api';
import { timestamp } from './data';
import { researchLabel } from './researchLabels';

export interface Artifact { artifact_id: string; kind: string; media_type: string; content_hash: string; byte_size: number; created_at: string }
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
type Preview = { type: 'report'; decisionId: string; profile: string; referenceOnly: boolean; analysts: string[]; attestation: string; narrative: string; structured: unknown; reportLanguage: string | null }
  | { type: 'evidence'; asOf: string; claims: { id: string; claim: string; sources: Source[] }[] };

function parse(value: unknown, artifact: Artifact, runId: string): Preview {
  const data = object(value);
  if (data.run_id !== runId) throw new ApiError(502);
  if (artifact.kind === 'analysis_report') {
    const decisionId = text(data.decision_id);
    if (!uuid.test(decisionId) || typeof data.reference_only !== 'boolean') throw new ApiError(502);
    return { type: 'report', decisionId, profile: text(data.profile), referenceOnly: data.reference_only,
      analysts: list(data.selected_analysts).map(text), attestation: text(data.snapshot_attestation),
      narrative: text(data.narrative), structured: data.structured_narrative,
      reportLanguage: ['en', 'vi', 'en-vi'].includes(String(data.report_language)) ? String(data.report_language) : null };
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

export default function ArtifactPreview({ artifact, runId }: { artifact: Artifact; runId: string }) {
  useLocale();
  const [open, setOpen] = useState(false);
  const supported = artifact.media_type === 'application/json' && ['analysis_report', 'decision_evidence'].includes(artifact.kind)
    && Number.isSafeInteger(artifact.byte_size) && artifact.byte_size > 0 && artifact.byte_size <= MAX_PREVIEW_BYTES;
  return <>
    {supported ? <button onClick={() => setOpen(value => !value)} aria-expanded={open}>{open ? t("Close") : t("Inspect")} {t(artifact.kind.replaceAll('_', ' '))}</button>
      : <p className="muted caption">{t("Inline preview unavailable for this format or size; use the integrity-checked download.")}</p>}
    {open && supported ? <PreviewBody key={`${runId}:${artifact.artifact_id}`} artifact={artifact} runId={runId} /> : null}
  </>;
}

function PreviewBody({ artifact, runId }: { artifact: Artifact; runId: string }) {
  useLocale();
  const [state, setState] = useState<{ data?: Preview; error?: unknown }>({});
  useEffect(() => {
    const controller = new AbortController();
    request<unknown>(`/artifacts/${encodeURIComponent(artifact.artifact_id)}`, { signal: controller.signal }, MAX_PREVIEW_BYTES)
      .then(value => parse(value, artifact, runId))
      .then(data => { if (!controller.signal.aborted) setState({ data }); })
      .catch(error => { if (!controller.signal.aborted) setState({ error }); });
    return () => controller.abort();
  }, [artifact, runId]);
  if (state.error) return <p role="alert" className="danger">{t("Preview unavailable.")} {t(errorMessage(state.error))}  {t("No report contents are shown.")}</p>;
  if (!state.data) return <p role="status">{t("Loading verified artifact…")}</p>;
  const data = state.data;
  return <section className="artifact-preview" aria-label={`${t(artifact.kind.replaceAll('_', ' '))} preview`}>
    <p className="muted caption">{t("Immutable research artifact · Not current approval state. Text is displayed without executing HTML or external content.")}</p>
    {data.type === 'report' ? <>
      <p>{t("Profile:")} {t(data.profile)} {t("· Analysts:")} {data.analysts.map(researchLabel).join(', ')}</p>
      {data.referenceOnly ? <p className="warning">{t("Reference only — not investable.")}</p> : null}
      <p>{t("Snapshot attestation:")} {data.attestation}</p>
      <h4>{t("Research narrative")}</h4>
      <p className="muted caption">{t('Original report · Language requested:')} {t(data.reportLanguage === 'en-vi' ? 'English + Vietnamese' : data.reportLanguage === 'vi' ? 'Vietnamese' : data.reportLanguage === 'en' ? 'English' : 'Legacy / not recorded')}</p>
      <p className="narrative" lang={data.reportLanguage === 'vi' ? 'vi' : data.reportLanguage === 'en' ? 'en' : undefined}>{data.narrative}</p>
      <p className="muted caption">{t('Original analysis text is preserved. Language preference guides generation; translation accuracy still requires human review.')}</p>
      <details><summary>{t("Structured research output")}</summary><pre className="safe-text">{JSON.stringify(data.structured ?? null, null, 2)}</pre></details>
      <a className="action-link" href={`#/decisions?decision=${encodeURIComponent(data.decisionId)}`}>{t("Review linked decision")}</a>
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
