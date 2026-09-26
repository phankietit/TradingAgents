import { useState } from 'react';
import { ApiError, errorMessage } from './api';
import { number, percent, timestamp, useResource } from './data';
import type { Artifact } from './ArtifactPreview';

interface Candidate { rank: number; instrument_id: string; canonical_symbol: string; source_snapshot_id: string;
  market_cap_usd: number; average_dollar_volume_20d_usd: number; annualized_volatility: number;
  ranking_score: number; market_cap_rank: number; liquidity_rank: number }
interface Exclusion { instrument_id: string; canonical_symbol: string; codes: string[]; reasons: string[] }
interface Screening { screening_snapshot_id: string; as_of: string; generated_at: string; input_count: number;
  input_hash: string; universe_hash: string; policy: { policy_id: string; schema_version: string } & Record<string, unknown>;
  candidates: Candidate[]; exclusions: Exclusion[] }

function validate(value: Screening): Screening {
  const text = (value: unknown) => typeof value === 'string';
  try {
    if (![value.screening_snapshot_id, value.as_of, value.generated_at, value.input_hash, value.universe_hash, value.policy.policy_id, value.policy.schema_version].every(text)
      || !Number.isSafeInteger(value.input_count) || !Array.isArray(value.candidates) || !Array.isArray(value.exclusions)
      || value.input_count !== value.candidates.length + value.exclusions.length
      || value.candidates.some((row, index) => !row || row.rank !== index + 1 ||
        ![row.instrument_id, row.canonical_symbol, row.source_snapshot_id].every(text) ||
        ![row.market_cap_usd, row.average_dollar_volume_20d_usd, row.annualized_volatility, row.ranking_score, row.market_cap_rank, row.liquidity_rank].every(Number.isFinite))
      || value.exclusions.some(row => !row || ![row.instrument_id, row.canonical_symbol].every(text) ||
        !Array.isArray(row.codes) || !row.codes.every(text) || !Array.isArray(row.reasons) || !row.reasons.every(text) || !row.codes.length || row.codes.length !== row.reasons.length)) throw new ApiError(502);
  } catch { throw new ApiError(502); }
  return value;
}

export default function StockScreener() {
  const [version, setVersion] = useState(0);
  const history = useResource<Artifact[]>('/screenings?limit=200', version, validateHistory);
  const [selected, setSelected] = useState('');
  const current = history.data?.find(item => item.artifact_id === selected) ?? history.data?.[0];
  return <section className="screening-panel" aria-label="Deterministic stock screener">
    <div className="section-actions"><h2>Screened stock candidates</h2><button onClick={() => setVersion(value => value + 1)}>Reload saved screenings</button></div>
    <p className="muted">Saved deterministic equity screening · No model ranking, live refresh, allocation or buy recommendation. Eligibility belongs to the saved as-of time; new analysis verifies its own source coverage.</p>
    {history.loading ? <p role="status">Loading screening history…</p> : history.error ? <p role="alert" className="danger">{errorMessage(history.error)}</p> : !history.data?.length ? <p className="notice">No owner screening snapshots. Generate and persist a screening with the existing operator workflow; no candidates are invented.</p> : <>
      <label className="snapshot-selector">Screening snapshot<select value={current?.artifact_id ?? ''} onChange={event => setSelected(event.target.value)}>{history.data.map(item => <option key={item.artifact_id} value={item.artifact_id}>{timestamp(item.created_at)} · {item.artifact_id.slice(0, 8)}</option>)}</select></label>
      {history.data.length === 200 ? <p className="warning">Latest 200 snapshots shown; older history is not loaded.</p> : null}
      {current ? <ScreeningDetail key={current.artifact_id} id={current.artifact_id} version={version} /> : null}
    </>}
  </section>;
}

function validateHistory(value: Artifact[]): Artifact[] {
  if (!Array.isArray(value) || value.some(row => !row || typeof row.artifact_id !== 'string' || typeof row.created_at !== 'string')) throw new ApiError(502);
  return value;
}

function ScreeningDetail({ id, version }: { id: string; version: number }) {
  const result = useResource<Screening>(`/screenings/${encodeURIComponent(id)}`, version, validate);
  const [showExcluded, setShowExcluded] = useState(false);
  const [page, setPage] = useState(0);
  if (result.loading) return <p role="status">Verifying saved screening…</p>;
  if (result.error || !result.data || result.data.screening_snapshot_id !== id) return <p role="alert" className="danger">Screening unavailable. {errorMessage(result.error)} No eligible universe is implied.</p>;
  const data = result.data;
  const count = showExcluded ? data.exclusions.length : data.candidates.length;
  return <>
    <p>As of {timestamp(data.as_of)} · Generated {timestamp(data.generated_at)} · {data.input_count} inputs</p>
    <p>Policy: {data.policy.policy_id}</p>
    <details className="provenance"><summary>Screening policy & provenance</summary>
      <p>Policy {data.policy.policy_id} · Schema {data.policy.schema_version}</p><pre className="safe-text">{JSON.stringify(data.policy, null, 2)}</pre>
      <dl><dt>Input hash</dt><dd className="mono">{data.input_hash}</dd><dt>Universe hash</dt><dd className="mono">{data.universe_hash}</dd><dt>Snapshot</dt><dd className="mono">{id}</dd></dl>
      <p className="muted">Artifact bytes, schema and universe hash are checked by the API. This does not prove live freshness or independently revalidate the original input facts. Source IDs are retained for audit.</p>
    </details>
    <div className="section-actions"><button aria-pressed={!showExcluded} onClick={() => { setShowExcluded(false); setPage(0); }}>Candidates ({data.candidates.length})</button><button aria-pressed={showExcluded} onClick={() => { setShowExcluded(true); setPage(0); }}>Excluded ({data.exclusions.length})</button></div>
    {!count ? <p className="notice">{showExcluded ? 'No exclusions recorded in this snapshot.' : 'No equities met this saved policy. This is an empty result, not missing screening data.'}</p> : <>
      <div className="table-scroll" role="region" aria-label={showExcluded ? 'Screening exclusions' : 'Screening candidates'} tabIndex={0}><table>
        <caption>{showExcluded ? 'Explicit exclusion reasons' : 'Backend ranking · USD values · Score is not expected return'}</caption>
        {showExcluded ? <><thead><tr><th>Symbol</th><th>Reasons</th></tr></thead><tbody>{data.exclusions.slice(page * 25, (page + 1) * 25).map(row => <tr key={row.instrument_id}><th scope="row">{row.canonical_symbol}</th><td className="wrap-cell">{row.codes.map((code, i) => <p key={code}>{code}: {row.reasons[i]}</p>)}</td></tr>)}</tbody></> : <>
          <thead><tr>{['Rank / symbol', 'Market cap (USD)', 'ADV 20d (USD)', 'Volatility', 'Rank score', 'Source / research'].map(label => <th key={label}>{label}</th>)}</tr></thead><tbody>{data.candidates.slice(page * 25, (page + 1) * 25).map(row => <tr key={row.instrument_id}>
            <th scope="row">{row.rank} · {row.canonical_symbol}</th><td>{number(row.market_cap_usd, 0)}</td><td>{number(row.average_dollar_volume_20d_usd, 0)}</td><td>{percent(row.annualized_volatility)}</td><td>{row.ranking_score}<small>Cap {row.market_cap_rank} · Liquidity {row.liquidity_rank}</small></td>
            <td className="wrap-cell"><span className="mono caption">{row.source_snapshot_id}</span><br /><a href={`#/analysis?instrument=${encodeURIComponent(row.instrument_id)}`}>Configure research</a></td>
          </tr>)}</tbody></>}
      </table></div>
      <div className="pagination"><button disabled={page === 0} onClick={() => setPage(value => value - 1)}>Previous screening rows</button><span>Page {page + 1} / {Math.ceil(count / 25)}</span><button disabled={(page + 1) * 25 >= count} onClick={() => setPage(value => value + 1)}>Next screening rows</button></div>
    </>}
  </>;
}
