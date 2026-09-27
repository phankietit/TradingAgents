import { t, useLocale, formatLocale } from './i18n';
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
  useLocale();
  const fields=policyFields.filter(([key])=>Object.hasOwn(policy.parameters,key));
  return <>
    {fields.length ? <div className="table-scroll policy-limits" role="region" aria-label={`${policy.name} ${t("limits")}`} tabIndex={0}><table><thead><tr><th>{t("Risk limit")}</th><th>{t("Saved value")}</th></tr></thead><tbody>{fields.map(([key,label,unit])=>{
      const value=policy.parameters[key];
      const valid=(typeof value==='number' || typeof value==='string' && value.trim()!=='') && Number.isFinite(Number(value));
      return <tr key={key}><th scope="row">{t(label)}</th><td>{!valid ? t("Unavailable — check policy details") : unit==='percent' ? percent(Number(value)) : `${value}${unit==='seconds' ? t(" seconds") : ''}`}</td></tr>;
    })}</tbody></table></div> : <p className="warning">{t("No recognized financial limits to summarize. Inspect the saved policy details before relying on it.")}</p>}
    <p className="muted">{t("Read-only saved limits, not a new policy or a risk-check result. Correlation is a coefficient, not a percentage.")}</p>
    <details><summary>{t("Policy audit details")}</summary><p className="mono">{policy.policy_id}</p><pre className="safe-text">{JSON.stringify(policy.parameters,null,2)}</pre><p>{t("All original parameters, including settings not summarized above.")}</p></details>
  </>;
}

/** Format persisted decimal strings without binary floating-point portfolio math. */
export function decimal(value: string | null | undefined): string {
  const plain = plainDecimal(value);
  if (plain === null) return t('Unavailable');
  const [integer, fraction] = plain.split('.');
  return integer.replace(/\B(?=(\d{3})+(?!\d))/g, formatLocale() === 'vi-VN' ? '.' : ',') + (fraction ? `${formatLocale() === 'vi-VN' ? ',' : '.'}${fraction}` : '');
}
export default function Portfolio() {
  useLocale();
  const [version, setVersion] = useState(0);
  const snapshots = useResource<PortfolioSnapshot[]>('/portfolios?limit=200', version, portfolioSnapshots);
  const catalog = useResource<Instrument[]>('/instruments?limit=500', 0, instruments);
  const policies = useResource<Policy[]>('/policies?limit=200', version, policyHistory);
  const [selected, setSelected] = useState('');
  const current = snapshots.data?.find(item => item.portfolio_id === selected) ?? snapshots.data?.[0];
  return <>
    <div className="section-actions"><p className="muted">{t("Saved portfolio valuations · Historical records, not a live account balance.")}</p><button onClick={() => setVersion(value => value + 1)}>{t("Reload portfolio")}</button></div>
    {snapshots.loading ? <p role="status">{t("Loading portfolio snapshots…")}</p> : snapshots.error ? <p role="alert" className="danger">{t(errorMessage(snapshots.error))}</p>
      : !current ? <section className="empty-state"><h2>{t("No portfolio snapshot")}</h2><p>{t("Import the owner ledger and create a valued snapshot through the backend portfolio workflow. Missing valuation is not shown as zero.")}</p></section>
      : <>
        <label className="snapshot-selector">{t("Portfolio snapshot")}<select value={current.portfolio_id} onChange={event => setSelected(event.target.value)}>{snapshots.data?.map((item,index) => <option key={item.portfolio_id} value={item.portfolio_id}>{timestamp(item.as_of)} · {item.base_currency}  {t("· Record")} {index+1}</option>)}</select></label>
        <p className="muted">{t("Valued as of")} {timestamp(current.as_of)}  {t("· Base currency")} {current.base_currency}</p>
        <div className="metrics portfolio-metrics"><div><span>{t("Net asset value ·")} {current.base_currency}</span><strong>{decimal(current.net_asset_value)}</strong></div>
          <div><span>{t("Realized P/L ·")} {current.base_currency}</span><strong>{decimal(current.realized_pnl)}</strong></div><div><span>{t("Unrealized P/L ·")} {current.base_currency}</span><strong>{decimal(current.unrealized_pnl)}</strong></div></div>
        <h2>{t("Cash")}</h2><div className="table-scroll" role="region" aria-label={t("Cash balances")} tabIndex={0}><table><thead><tr><th>{t("Currency")}</th><th>{t("Balance")}</th></tr></thead><tbody>{current.cash.map(item => <tr key={item.currency}><th scope="row">{item.currency}</th><td>{decimal(item.amount)}</td></tr>)}</tbody></table></div>
        {!current.cash.length ? <p className="muted">{t("No cash balance entries in this snapshot.")}</p> : null}
        <h2>{t("Holdings & allocation")}</h2>
        <ValuationSources key={current.portfolio_id} id={current.portfolio_id} hash={current.content_hash} catalog={catalog.data ?? []} />
        {catalog.error ? <p className="warning">{t("Instrument names unavailable; persisted instrument IDs are shown.")}</p> : null}
        {!current.positions.length ? <p className="muted">{t("This snapshot contains no positions.")}</p> : <div className="table-scroll" role="region" aria-label={t("Portfolio holdings")} tabIndex={0}><table><thead><tr>{['Instrument', 'Quantity', 'Average cost', 'Valuation price', 'Market value', 'Weight'].map(label => <th key={label} scope="col">{t(label)}</th>)}</tr></thead><tbody>{current.positions.map(item => {
          const asset = catalog.data?.find(value => value.instrument_id === item.instrument_id);
          return <tr key={item.instrument_id}><th scope="row">{asset?.canonical_symbol ?? item.instrument_id}</th><td>{decimal(item.quantity)}</td><td>{decimal(item.average_price)}</td><td>{decimal(item.market_price)}</td><td>{decimal(item.market_value)} {current.base_currency}</td><td>{percent(Number(item.weight))}</td></tr>;
        })}</tbody></table></div>}
        <details className="provenance"><summary>{t("Snapshot identity")}</summary><p className="mono">{current.portfolio_id}</p><p className="mono">{current.content_hash}</p><p className="muted">{t("Holdings, cash, P/L and weights are persisted backend values. This page does not rebalance or rewrite portfolio history.")}</p></details>
      </>}
    {snapshots.data?.length === 200 ? <p className="warning">{t("Showing the latest 200 snapshots.")}</p> : null}
    <section className="policy-section"><h2>{t("Policy versions")}</h2><p className="muted">{t("Read-only policy history. Each decision binds an exact version; this is not a permission to change risk limits.")}</p>
      {policies.loading ? <p role="status">{t("Loading policies…")}</p> : policies.error ? <p role="alert" className="danger">{t(errorMessage(policies.error))}</p>
        : !policies.data?.length ? <p className="muted">{t("No owner policy is configured. Approval-ready risk evaluation requires a governed policy.")}</p>
        : policies.data.map(policy => <details key={`${policy.policy_id}:${policy.policy_version}`} className="provenance"><summary>{policy.name}  {t("· v")}{policy.policy_version} · {t(policy.asset_class)}</summary><p>{t("Effective")} {timestamp(policy.effective_at)}</p><PolicyLimits policy={policy} /></details>)}
    </section>
  </>;
}
