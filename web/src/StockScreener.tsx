import { t, useLocale, formatLocale } from './i18n';
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

const compactUSD = () => new Intl.NumberFormat(formatLocale(), { style: 'currency', currency: 'USD', notation: 'compact', maximumFractionDigits: 1 });

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
  useLocale();
  const [version, setVersion] = useState(0);
  const history = useResource<Artifact[]>('/screenings?limit=200', version, validateHistory);
  const [selected, setSelected] = useState('');
  const current = history.data?.find(item => item.artifact_id === selected) ?? history.data?.[0];
  return <section className="screening-panel" aria-label={t("Deterministic stock screener")}>
    <div className="section-actions"><h2>{t("Screened stock candidates")}</h2><button onClick={() => setVersion(value => value + 1)}>{t("Reload saved screenings")}</button></div>
    <p className="muted">{t("Stocks that met the saved financial criteria. Rankings are not return forecasts or recommendations to buy.")}</p>
    {history.loading ? <p role="status">{t("Loading screening history…")}</p> : history.error ? <p role="alert" className="danger">{t(errorMessage(history.error))}</p> : !history.data?.length ? <p className="notice">{t("No owner screening snapshots. Generate and persist a screening with the existing operator workflow; no candidates are invented.")}</p> : <>
      <label className="snapshot-selector">{t("Screening date")}<select value={current?.artifact_id ?? ''} onChange={event => setSelected(event.target.value)}>{history.data.map((item, index) => <option key={item.artifact_id} value={item.artifact_id}>{timestamp(item.created_at)}  {t("· Result")} {index + 1}</option>)}</select></label>
      {history.data.length === 200 ? <p className="warning">{t("Latest 200 snapshots shown; older history is not loaded.")}</p> : null}
      {current ? <ScreeningDetail key={current.artifact_id} id={current.artifact_id} version={version} /> : null}
    </>}
  </section>;
}

function validateHistory(value: Artifact[]): Artifact[] {
  if (!Array.isArray(value) || value.some(row => !row || typeof row.artifact_id !== 'string' || typeof row.created_at !== 'string')) throw new ApiError(502);
  return value;
}

function ScreeningDetail({ id, version }: { id: string; version: number }) {
  useLocale();
  const result = useResource<Screening>(`/screenings/${encodeURIComponent(id)}`, version, validate);
  const [showExcluded, setShowExcluded] = useState(false);
  const [page, setPage] = useState(0);
  if (result.loading) return <p role="status">{t("Verifying saved screening…")}</p>;
  if (result.error || !result.data || result.data.screening_snapshot_id !== id) return <p role="alert" className="danger">{t("Screening unavailable.")} {t(errorMessage(result.error))}  {t("No eligible universe is implied.")}</p>;
  const data = result.data;
  const count = showExcluded ? data.exclusions.length : data.candidates.length;
  return <>
    <p className="muted">{t("Data as of")} {timestamp(data.as_of)} · {data.input_count}  {t("instruments assessed")}</p>
    <p className="muted">{t("Saved results, not live prices. Eligibility may have changed; new research checks its own data.")}</p>
    {/synthetic|fixture/i.test(data.policy.policy_id) ? <p className="warning">{t("Sample data · Illustrative screening only, not your investment policy.")}</p> : null}
    <details className="provenance"><summary>{t("How to read these results")}</summary>
      <p>{t("Market cap is company equity value. Average daily trading value measures liquidity over 20 days. Annualized volatility describes price variability, not a return forecast.")}</p>
      <p>{t("Rank follows the saved screening policy. Review business fundamentals, valuation and portfolio risk before making an investment decision.")}</p>
    </details>
    <details className="provenance"><summary>{t("Screening policy & provenance")}</summary>
      <p>{t("Generated")} {timestamp(data.generated_at)}</p>
      <p>{t("Policy")} {data.policy.policy_id}  {t("· Schema")} {data.policy.schema_version}</p><pre className="safe-text">{JSON.stringify(data.policy, null, 2)}</pre>
      <dl><dt>{t("Input hash")}</dt><dd className="mono">{data.input_hash}</dd><dt>{t("Universe hash")}</dt><dd className="mono">{data.universe_hash}</dd><dt>{t("Snapshot")}</dt><dd className="mono">{id}</dd></dl>
      <p className="muted">{t("Artifact bytes, schema and universe hash are checked by the API. This does not prove live freshness or independently revalidate the original input facts. Source IDs are retained for audit.")}</p>
    </details>
    <div className="section-actions"><button aria-pressed={!showExcluded} onClick={() => { setShowExcluded(false); setPage(0); }}>{t("Candidates (")}{data.candidates.length})</button><button aria-pressed={showExcluded} onClick={() => { setShowExcluded(true); setPage(0); }}>{t("Excluded (")}{data.exclusions.length})</button></div>
    {!count ? <p className="notice">{showExcluded ? t("No exclusions recorded in this snapshot.") : t("No equities met this saved policy. This is an empty result, not missing screening data.")}</p> : <>
      <div className="table-scroll" role="region" aria-label={showExcluded ? t("Screening exclusions") : t("Screening candidates")} tabIndex={0}><table>
        <caption>{showExcluded ? t("Why these instruments did not qualify") : t("Ranked by saved criteria · Values in USD")}</caption>
        {showExcluded ? <><thead><tr><th>{t("Symbol")}</th><th>{t("Reasons")}</th></tr></thead><tbody>{data.exclusions.slice(page * 25, (page + 1) * 25).map(row => <tr key={row.instrument_id}><th scope="row">{row.canonical_symbol}</th><td className="wrap-cell">{row.reasons.map((reason, i) => <p key={i}>{reason}</p>)}<details><summary>{t("Audit details")}</summary><p className="mono">{row.codes.join(', ')}</p></details></td></tr>)}</tbody></> : <>
          <thead><tr>{['Rank / symbol', 'Market cap', 'Daily trading value · 20d avg.', 'Volatility · annualized', 'Research'].map(label => <th key={label}>{t(label)}</th>)}</tr></thead><tbody>{data.candidates.slice(page * 25, (page + 1) * 25).map(row => <tr key={row.instrument_id}>
            <th scope="row">{row.rank} · {row.canonical_symbol}</th><td><span title={`${number(row.market_cap_usd, 0)} USD`}>{compactUSD().format(row.market_cap_usd)}</span></td><td><span title={`${number(row.average_dollar_volume_20d_usd, 0)} USD`}>{compactUSD().format(row.average_dollar_volume_20d_usd)}</span></td><td>{percent(row.annualized_volatility)}</td>
            <td><a href={`#/analysis?instrument=${encodeURIComponent(row.instrument_id)}`}>{t("Configure research")}</a><details className="screening-audit"><summary>{t("Audit details")}</summary><dl><dt>{t("Market cap · USD")}</dt><dd>{number(row.market_cap_usd, 0)}</dd><dt>{t("Daily trading value · USD")}</dt><dd>{number(row.average_dollar_volume_20d_usd, 0)}</dd><dt>{t("Ranking score")}</dt><dd>{row.ranking_score}</dd><dt>{t("Market cap rank")}</dt><dd>{row.market_cap_rank}</dd><dt>{t("Liquidity rank")}</dt><dd>{row.liquidity_rank}</dd><dt>{t("Source ID")}</dt><dd className="mono">{row.source_snapshot_id}</dd></dl></details></td>
          </tr>)}</tbody></>}
      </table></div>
      <div className="pagination"><button disabled={page === 0} onClick={() => setPage(value => value - 1)}>{t("Previous screening rows")}</button><span>{t("Page")} {page + 1} / {Math.ceil(count / 25)}</span><button disabled={(page + 1) * 25 >= count} onClick={() => setPage(value => value + 1)}>{t("Next screening rows")}</button></div>
    </>}
  </>;
}
