import { useState } from 'react';
import { ApiError, errorMessage } from './api';
import { timestamp, useResource } from './data';
import type { Instrument } from './data';
import { plainDecimal } from './decimal';

interface Evidence {portfolio_id: string; portfolio_content_hash: string; sources: {vendor: string; dataset: string;
  quote: {instrument_id: string; price: string; currency: string; source_at: string; observed_at: string; quality_status: string; snapshot_id: string; content_hash: string}}[]}
function validate(value: Evidence): Evidence {
  if (!value || typeof value.portfolio_id !== 'string' || typeof value.portfolio_content_hash !== 'string' || !Array.isArray(value.sources)
    || value.sources.some(source=> !source || typeof source.vendor !== 'string' || typeof source.dataset !== 'string' || !source.quote
      || ![source.quote.instrument_id,source.quote.price,source.quote.currency,source.quote.quality_status,source.quote.snapshot_id,source.quote.content_hash].every(item=>typeof item==='string')
      || plainDecimal(source.quote.price) === null
      || ![source.quote.source_at,source.quote.observed_at].every(item=>typeof item==='string' && Number.isFinite(Date.parse(item))))) throw new ApiError(502);
  return value;
}
export default function ValuationSources({id, hash, catalog}: {id: string; hash: string; catalog: Instrument[]}) {
  const [open,setOpen] = useState(false);
  return <section aria-label="Valuation sources"><button aria-expanded={open} onClick={()=>setOpen(value=>!value)}>{open ? 'Hide valuation sources' : 'View valuation sources'}</button>
    {open ? <Sources id={id} hash={hash} catalog={catalog} /> : null}</section>;
}
function Sources({id,hash,catalog}: {id: string; hash: string; catalog: Instrument[]}) {
  const result=useResource<Evidence>(`/portfolios/${encodeURIComponent(id)}/valuation-evidence`,0,validate);
  if(result.loading) return <p role="status">Checking saved valuation sources…</p>;
  if(result.error || !result.data || result.data.portfolio_id!==id || result.data.portfolio_content_hash!==hash) return <p className="warning">Valuation sources unavailable. {result.error instanceof ApiError && result.error.status===404 ? 'This saved portfolio has no source receipt. Its price sources cannot be verified here.' : errorMessage(result.error)} No current price has been substituted.</p>;
  return <><p className="muted">Prices recorded when this portfolio was valued. This is historical evidence, not a live quote or a new valuation.</p>
    {!result.data.sources.length ? <p>No security prices were required for this cash-only valuation.</p> : result.data.sources.map(source=><div className="provenance" key={source.quote.instrument_id}>
      <h3>{catalog.find(asset=>asset.instrument_id===source.quote.instrument_id)?.canonical_symbol ?? 'Holding'} · {plainDecimal(source.quote.price)} {source.quote.currency}</h3>
      <p>{source.vendor} · Recorded quality: {source.quote.quality_status}</p>
      <p>Price time {timestamp(source.quote.source_at)} · Retrieved {timestamp(source.quote.observed_at)}</p>
      <details><summary>Source audit details</summary><dl><dt>Dataset</dt><dd>{source.dataset}</dd><dt>Source ID</dt><dd className="mono">{source.quote.snapshot_id}</dd><dt>Content hash</dt><dd className="mono">{source.quote.content_hash}</dd></dl></details>
    </div>)}</>;
}
