import { useEffect, useState } from 'react';
import { ApiError, errorMessage, request } from './api';
import { timestamp } from './data';

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
type Preview = { type: 'report'; decisionId: string; profile: string; referenceOnly: boolean; analysts: string[]; attestation: string; narrative: string; structured: unknown }
  | { type: 'evidence'; asOf: string; claims: { id: string; claim: string; sources: Source[] }[] };

function parse(value: unknown, artifact: Artifact, runId: string): Preview {
  const data = object(value);
  if (data.run_id !== runId) throw new ApiError(502);
  if (artifact.kind === 'analysis_report') {
    const decisionId = text(data.decision_id);
    if (!uuid.test(decisionId) || typeof data.reference_only !== 'boolean') throw new ApiError(502);
    return { type: 'report', decisionId, profile: text(data.profile), referenceOnly: data.reference_only,
      analysts: list(data.selected_analysts).map(text), attestation: text(data.snapshot_attestation),
      narrative: text(data.narrative), structured: data.structured_narrative };
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
  const [open, setOpen] = useState(false);
  const supported = artifact.media_type === 'application/json' && ['analysis_report', 'decision_evidence'].includes(artifact.kind)
    && Number.isSafeInteger(artifact.byte_size) && artifact.byte_size > 0 && artifact.byte_size <= MAX_PREVIEW_BYTES;
  return <>
    {supported ? <button onClick={() => setOpen(value => !value)} aria-expanded={open}>{open ? 'Close' : 'Inspect'} {artifact.kind.replaceAll('_', ' ')}</button>
      : <p className="muted caption">Inline preview unavailable for this format or size; use the integrity-checked download.</p>}
    {open && supported ? <PreviewBody key={`${runId}:${artifact.artifact_id}`} artifact={artifact} runId={runId} /> : null}
  </>;
}

function PreviewBody({ artifact, runId }: { artifact: Artifact; runId: string }) {
  const [state, setState] = useState<{ data?: Preview; error?: unknown }>({});
  useEffect(() => {
    const controller = new AbortController();
    request<unknown>(`/artifacts/${encodeURIComponent(artifact.artifact_id)}`, { signal: controller.signal }, MAX_PREVIEW_BYTES)
      .then(value => parse(value, artifact, runId))
      .then(data => { if (!controller.signal.aborted) setState({ data }); })
      .catch(error => { if (!controller.signal.aborted) setState({ error }); });
    return () => controller.abort();
  }, [artifact, runId]);
  if (state.error) return <p role="alert" className="danger">Preview unavailable. {errorMessage(state.error)} No report contents are shown.</p>;
  if (!state.data) return <p role="status">Loading verified artifact…</p>;
  const data = state.data;
  return <section className="artifact-preview" aria-label={`${artifact.kind.replaceAll('_', ' ')} preview`}>
    <p className="muted caption">Immutable research artifact · Not current approval state. Text is displayed without executing HTML or external content.</p>
    {data.type === 'report' ? <>
      <p>Profile: {data.profile} · Analysts: {data.analysts.join(', ')}</p>
      {data.referenceOnly ? <p className="warning">Reference only — not investable.</p> : null}
      <p>Snapshot attestation: {data.attestation}</p>
      <h4>Research narrative</h4><p className="narrative">{data.narrative}</p>
      <details><summary>Structured research output</summary><pre className="safe-text">{JSON.stringify(data.structured ?? null, null, 2)}</pre></details>
      <a className="action-link" href={`#/decisions?decision=${encodeURIComponent(data.decisionId)}`}>Review linked decision</a>
    </> : <>
      <p>Evidence as of {timestamp(data.asOf)}</p>
      {!data.claims.length ? <p className="warning">No material claims are linked. This is not evidence of a valid conclusion.</p> : data.claims.map(claim => <details key={claim.id}>
        <summary>{claim.claim}</summary>{claim.sources.map(source => <dl key={source.id}>
          <dt>Source</dt><dd>{source.name}</dd><dt>Source time</dt><dd>{timestamp(source.sourceAt)}</dd>
          <dt>Observed</dt><dd>{timestamp(source.observedAt)}</dd><dt>Snapshot</dt><dd className="mono">{source.snapshot}</dd>
          <dt>Content hash</dt><dd className="mono">{source.hash}</dd>
        </dl>)}
      </details>)}
    </>}
  </section>;
}
