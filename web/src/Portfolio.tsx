import { useState } from 'react';
import { errorMessage } from './api';
import { instruments, percent, timestamp, useResource } from './data';
import type { Instrument } from './data';
import ValuationSources from './ValuationSources';
import { portfolioSnapshots, policyHistory } from './portfolioData';
import { plainDecimal } from './decimal';

export interface PortfolioSnapshot {
  portfolio_id: string; as_of: string; base_currency: string; net_asset_value: string;
  realized_pnl: string; unrealized_pnl: string; content_hash: string;
  cash: { currency: string; amount: string }[];
  positions: { instrument_id: string; quantity: string; average_price: string | null;
    market_price: string; market_value: string; weight: number | string }[];
}
export interface Policy { policy_id: string; policy_version: string; name: string; asset_class: string; effective_at: string; parameters: Record<string, unknown> }

const policyFields: [string, string, 'percent' | 'number' | 'seconds'][] = [
  ['max_position_weight','Maximum position allocation','percent'],
  ['max_asset_class_weight','Maximum asset-class allocation','percent'],
  ['max_gross_exposure','Maximum total exposure','percent'],
  ['max_turnover','Maximum portfolio turnover','percent'],
  ['min_cash_weight','Minimum cash reserve','percent'],
  ['max_correlation','Maximum holding correlation','number'],
  ['correlation_periods','Correlation observation periods','number'],
  ['correlation_max_age_seconds','Maximum correlation source age','seconds'],
];
function PolicyLimits({policy}: {policy: Policy}) {
  const fields=policyFields.filter(([key])=>Object.hasOwn(policy.parameters,key));
  return <>
    {fields.length ? <div className="table-scroll policy-limits" role="region" aria-label={`${policy.name} limits`} tabIndex={0}><table><thead><tr><th>Risk limit</th><th>Saved value</th></tr></thead><tbody>{fields.map(([key,label,unit])=>{
      const value=policy.parameters[key];
      const valid=(typeof value==='number' || typeof value==='string' && value.trim()!=='') && Number.isFinite(Number(value));
      return <tr key={key}><th scope="row">{label}</th><td>{!valid ? 'Unavailable — check policy details' : unit==='percent' ? percent(Number(value)) : `${value}${unit==='seconds' ? ' seconds' : ''}`}</td></tr>;
    })}</tbody></table></div> : <p className="warning">No recognized financial limits to summarize. Inspect the saved policy details before relying on it.</p>}
    <p className="muted">Read-only saved limits, not a new policy or a risk-check result. Correlation is a coefficient, not a percentage.</p>
    <details><summary>Policy audit details</summary><p className="mono">{policy.policy_id}</p><pre className="safe-text">{JSON.stringify(policy.parameters,null,2)}</pre><p>All original parameters, including settings not summarized above.</p></details>
  </>;
}

/** Format persisted decimal strings without binary floating-point portfolio math. */
export function decimal(value: string | null | undefined): string {
  const plain = plainDecimal(value);
  if (plain === null) return 'Unavailable';
  const [integer, fraction] = plain.split('.');
  return integer.replace(/\B(?=(\d{3})+(?!\d))/g, ',') + (fraction ? `.${fraction}` : '');
}
export default function Portfolio() {
  const [version, setVersion] = useState(0);
  const snapshots = useResource<PortfolioSnapshot[]>('/portfolios?limit=200', version, portfolioSnapshots);
  const catalog = useResource<Instrument[]>('/instruments?limit=500', 0, instruments);
  const policies = useResource<Policy[]>('/policies?limit=200', version, policyHistory);
  const [selected, setSelected] = useState('');
  const current = snapshots.data?.find(item => item.portfolio_id === selected) ?? snapshots.data?.[0];
  return <>
    <div className="section-actions"><p className="muted">Saved portfolio valuations · Historical records, not a live account balance.</p><button onClick={() => setVersion(value => value + 1)}>Reload portfolio</button></div>
    {snapshots.loading ? <p role="status">Loading portfolio snapshots…</p> : snapshots.error ? <p role="alert" className="danger">{errorMessage(snapshots.error)}</p>
      : !current ? <section className="empty-state"><h2>No portfolio snapshot</h2><p>Import the owner ledger and create a valued snapshot through the backend portfolio workflow. Missing valuation is not shown as zero.</p></section>
      : <>
        <label className="snapshot-selector">Portfolio snapshot<select value={current.portfolio_id} onChange={event => setSelected(event.target.value)}>{snapshots.data?.map((item,index) => <option key={item.portfolio_id} value={item.portfolio_id}>{timestamp(item.as_of)} · {item.base_currency} · Record {index+1}</option>)}</select></label>
        <p className="muted">Valued as of {timestamp(current.as_of)} · Base currency {current.base_currency}</p>
        <div className="metrics portfolio-metrics"><div><span>Net asset value · {current.base_currency}</span><strong>{decimal(current.net_asset_value)}</strong></div>
          <div><span>Realized P/L · {current.base_currency}</span><strong>{decimal(current.realized_pnl)}</strong></div><div><span>Unrealized P/L · {current.base_currency}</span><strong>{decimal(current.unrealized_pnl)}</strong></div></div>
        <h2>Cash</h2><div className="table-scroll" role="region" aria-label="Cash balances" tabIndex={0}><table><thead><tr><th>Currency</th><th>Balance</th></tr></thead><tbody>{current.cash.map(item => <tr key={item.currency}><th scope="row">{item.currency}</th><td>{decimal(item.amount)}</td></tr>)}</tbody></table></div>
        {!current.cash.length ? <p className="muted">No cash balance entries in this snapshot.</p> : null}
        <h2>Holdings & allocation</h2>
        <ValuationSources key={current.portfolio_id} id={current.portfolio_id} hash={current.content_hash} catalog={catalog.data ?? []} />
        {catalog.error ? <p className="warning">Instrument names unavailable; persisted instrument IDs are shown.</p> : null}
        {!current.positions.length ? <p className="muted">This snapshot contains no positions.</p> : <div className="table-scroll" role="region" aria-label="Portfolio holdings" tabIndex={0}><table><thead><tr>{['Instrument', 'Quantity', 'Average cost', 'Valuation price', 'Market value', 'Weight'].map(label => <th key={label} scope="col">{label}</th>)}</tr></thead><tbody>{current.positions.map(item => {
          const asset = catalog.data?.find(value => value.instrument_id === item.instrument_id);
          return <tr key={item.instrument_id}><th scope="row">{asset?.canonical_symbol ?? item.instrument_id}</th><td>{decimal(item.quantity)}</td><td>{decimal(item.average_price)}</td><td>{decimal(item.market_price)}</td><td>{decimal(item.market_value)} {current.base_currency}</td><td>{percent(Number(item.weight))}</td></tr>;
        })}</tbody></table></div>}
        <details className="provenance"><summary>Snapshot identity</summary><p className="mono">{current.portfolio_id}</p><p className="mono">{current.content_hash}</p><p className="muted">Holdings, cash, P/L and weights are persisted backend values. This page does not rebalance or rewrite portfolio history.</p></details>
      </>}
    {snapshots.data?.length === 200 ? <p className="warning">Showing the latest 200 snapshots.</p> : null}
    <section className="policy-section"><h2>Policy versions</h2><p className="muted">Read-only policy history. Each decision binds an exact version; this is not a permission to change risk limits.</p>
      {policies.loading ? <p role="status">Loading policies…</p> : policies.error ? <p role="alert" className="danger">{errorMessage(policies.error)}</p>
        : !policies.data?.length ? <p className="muted">No owner policy is configured. Approval-ready risk evaluation requires a governed policy.</p>
        : policies.data.map(policy => <details key={`${policy.policy_id}:${policy.policy_version}`} className="provenance"><summary>{policy.name} · v{policy.policy_version} · {policy.asset_class}</summary><p>Effective {timestamp(policy.effective_at)}</p><PolicyLimits policy={policy} /></details>)}
    </section>
  </>;
}
