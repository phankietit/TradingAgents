import { useState } from 'react';
import { ApiError, errorMessage, mutate } from './api';
import { instruments, number, percent, timestamp, useResource } from './data';
import type { Instrument, SeriesResponse } from './data';

const groups = ['All assets', 'Stocks', 'ETFs', 'Crypto', 'Index references'] as const;
const groupOf = (item: Instrument) => item.asset_class === 'equity' ? 'Stocks' : item.asset_class === 'etf' ? 'ETFs'
  : item.asset_class === 'crypto' ? 'Crypto' : 'Index references';

export default function Markets() {
  const [version, setVersion] = useState(0);
  const catalog = useResource<Instrument[]>('/instruments?limit=500', version, instruments);
  const watchlist = useResource<Instrument[]>('/watchlist?limit=200', version, instruments);
  const [group, setGroup] = useState<string>('All assets');
  const [search, setSearch] = useState('');
  const [onlyWatched, setOnlyWatched] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const source = onlyWatched ? watchlist : catalog;
  const visible = (source.data ?? []).filter(item => (group === 'All assets' || groupOf(item) === group)
    && `${item.canonical_symbol} ${item.display_name}`.toLowerCase().includes(search.toLowerCase()));
  const instrument = visible.find(item => item.instrument_id === selected) ?? visible[0];
  const refresh = () => setVersion(value => value + 1);
  return <>
    <div className="market-toolbar">
      <label>Asset group<select value={group} onChange={event => setGroup(event.target.value)}>{groups.map(name => <option key={name}>{name}</option>)}</select></label>
      <label className="search-field">Find an instrument<input type="search" value={search} onChange={event => setSearch(event.target.value)} placeholder="Symbol or company name" /></label>
      <label className="checkbox-field"><input type="checkbox" checked={onlyWatched} onChange={event => setOnlyWatched(event.target.checked)} />Watchlist only</label>
      <button onClick={refresh}>Reload saved data</button>
    </div>
    <p className="muted caption">Saved snapshots · Not a live price feed. Reload reads the database; it does not call a market-data or model provider.</p>
    <div className="market-layout">
      <section className="instrument-list" aria-label="Instruments">
        <div className="list-heading">Instruments <span>{visible.length}</span></div>
        {source.loading ? <p role="status">Loading instruments…</p> : source.error ? <p role="alert" className="danger">{errorMessage(source.error)}</p>
          : visible.length === 0 ? <p className="muted">{source.data?.length ? 'No instruments match these filters.' : onlyWatched ? 'Your watchlist is empty. Browse all assets to save an instrument.' : 'No instruments have been configured. Import the instrument master before researching markets.'}</p>
          : <ul>{visible.map(item => <li key={item.instrument_id}><button onClick={() => setSelected(item.instrument_id)} aria-pressed={instrument?.instrument_id === item.instrument_id}>
            <span className="instrument-row"><strong>{item.canonical_symbol}</strong><span className="caption">{groupOf(item)}</span></span>
            <span className="instrument-name">{item.display_name}</span>
            {item.tradability === 'reference_only' ? <span className="warning caption">Reference only</span> : null}
          </button></li>)}</ul>}
        {source.data?.length === (onlyWatched ? 200 : 500) ? <p className="warning">Display limit reached; this list may be incomplete.</p> : null}
      </section>
      {instrument ? <InstrumentDetail key={instrument.instrument_id} instrument={instrument} version={version}
        watched={watchlist.data?.some(item => item.instrument_id === instrument.instrument_id)} watchlistError={watchlist.error}
        onWatchlistChange={refresh} /> : <section className="empty-state"><h2>Select an instrument</h2><p>Price history and source details will appear here when saved data is available.</p></section>}
    </div>
  </>;
}

function InstrumentDetail({ instrument, watched, watchlistError, version, onWatchlistChange }: {
  instrument: Instrument; watched: boolean | undefined; watchlistError: unknown; version: number; onWatchlistChange: () => void;
}) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const series = useResource<SeriesResponse>(`/instruments/${encodeURIComponent(instrument.instrument_id)}/timeseries`, version);
  async function toggleWatchlist() {
    if (watched === undefined) return;
    setPending(true); setError('');
    try { await mutate(`/watchlist/${encodeURIComponent(instrument.instrument_id)}`, undefined, watched ? 'DELETE' : 'PUT'); onWatchlistChange(); }
    catch (cause) { setError(errorMessage(cause)); }
    finally { setPending(false); }
  }
  return <section className="instrument-detail" aria-label={`${instrument.canonical_symbol} details`}>
    <div className="detail-heading"><div><h2>{instrument.canonical_symbol} <span className="muted">{instrument.display_name}</span></h2>
      <p className="muted caption">{instrument.venue} · {instrument.quote_currency} · {instrument.session_calendar} · {instrument.timezone}</p></div>
      <div className="section-actions"><button onClick={toggleWatchlist} disabled={pending || watched === undefined}>{pending ? 'Saving…' : watched ? 'Remove from watchlist' : 'Add to watchlist'}</button><a className="action-link" href={`#/analysis?instrument=${encodeURIComponent(instrument.instrument_id)}`}>Analyze</a></div></div>
    {instrument.tradability === 'reference_only' ? <p className="notice warning">Reference only — context for research, not an investable or executable instrument.</p> : null}
    {instrument.asset_class === 'crypto' ? <p className="notice">Crypto · 24/7 market calendar. Separate allocation and policy limits apply.</p> : null}
    {error || watchlistError ? <p role="alert" className="danger">{error || `Watchlist unavailable. ${errorMessage(watchlistError)}`}</p> : null}
    {series.loading ? <p role="status">Loading saved price history…</p> : series.error ? <div className="empty-state" role="status"><h2>Price history unavailable</h2><p>{series.error instanceof ApiError && series.error.status === 404 ? 'No owner-readable price snapshot is available. Ingest market data before analysis; no substitute prices are shown.' : errorMessage(series.error)}</p></div>
      : series.data ? <PriceHistory data={series.data} /> : null}
  </section>;
}

function PriceHistory({ data }: { data: SeriesResponse }) {
  const { snapshot, view } = data;
  const [showTable, setShowTable] = useState(false);
  const [page, setPage] = useState(0);
  const points = view.returns;
  // Chart geometry only. Returns, drawdown and volatility come from the backend.
  const valid = Array.isArray(points) && points.length > 0 && points.every(point => Number.isFinite(point.price) && Number.isFinite(Date.parse(point.timestamp)));
  if (!valid) return <p role="alert" className="danger">Price response is invalid; chart withheld.</p>;
  const prices = points.map(point => point.price);
  const minimum = prices.reduce((value, price) => Math.min(value, price), Infinity);
  const maximum = prices.reduce((value, price) => Math.max(value, price), -Infinity);
  const start = Date.parse(points[0].timestamp);
  const duration = Date.parse(points[points.length - 1].timestamp) - start || 1;
  const range = maximum - minimum || maximum * .02 || 1;
  const polyline = points.map(point => `${50 + (Date.parse(point.timestamp) - start) / duration * 820},${230 - (point.price - minimum) / range * 180}`).join(' ');
  const rows = view.series.bars.slice(page * 30, (page + 1) * 30);
  return <>
    <div className="quality-line"><span className={snapshot.quality_status === 'OK' ? 'muted' : 'warning'}>Snapshot quality: {snapshot.quality_status}</span><span>{snapshot.vendor}</span><span>Source through {timestamp(snapshot.source_end)}</span></div>
    {snapshot.quality_reasons.length ? <p className="notice warning">{snapshot.quality_reasons.join(' · ')}</p> : null}
    <div className="metrics">
      <div><span>Last saved price · {view.series.quote_currency}</span><strong>{number(points[points.length - 1].price)}</strong></div>
      <div><span>Period return</span><strong>{percent(view.statistics.total_return)}</strong></div>
      <div><span>Annualized volatility</span><strong>{percent(view.statistics.annualized_volatility)}</strong></div>
      <div><span>Maximum drawdown</span><strong>{percent(view.statistics.maximum_drawdown)}</strong></div>
    </div>
    <figure className="price-chart"><svg viewBox="0 0 900 280" role="img" aria-label={`Saved ${view.statistics.price_basis} history in ${view.series.quote_currency}; ${points.length} observations. Data table available below.`}>
      <line x1="50" x2="870" y1="230" y2="230" stroke="var(--border)" /><line x1="50" x2="870" y1="50" y2="50" stroke="var(--border)" />
      <text x="50" y="36">{number(maximum)} {view.series.quote_currency}</text><text x="50" y="252">{number(minimum)}</text>
      <polyline points={polyline} fill="none" stroke="var(--accent)" strokeWidth="2" vectorEffect="non-scaling-stroke" />
      {points.length === 1 ? <circle cx="50" cy="230" r="4" fill="var(--accent)" /> : null}
    </svg><figcaption>{timestamp(points[0].timestamp)} — {timestamp(points[points.length - 1].timestamp)}<br />{view.statistics.price_basis.replace('_', ' ')} · {view.series.interval} · {view.statistics.observations} observations</figcaption></figure>
    <button onClick={() => setShowTable(value => !value)} aria-expanded={showTable} aria-controls="price-table">{showTable ? 'Hide price table' : 'Show price table'}</button>
    {showTable ? <div id="price-table"><div className="table-scroll" role="region" aria-label="Saved OHLCV price history" tabIndex={0}><table><caption>Saved OHLCV · {view.series.quote_currency} · UTC timestamps</caption><thead><tr>{['Timestamp', 'Open', 'High', 'Low', 'Close', 'Adjusted close', 'Volume'].map(label => <th key={label} scope="col">{label}</th>)}</tr></thead><tbody>{rows.map(bar => <tr key={bar.timestamp}><th scope="row">{timestamp(bar.timestamp)}</th>{[bar.open, bar.high, bar.low, bar.close, bar.adjusted_close, bar.volume].map((value, index) => <td key={index}>{value === null ? 'Unavailable' : number(value, index === 5 ? 0 : 2)}</td>)}</tr>)}</tbody></table></div>
      <div className="pagination"><button disabled={page === 0} onClick={() => setPage(value => value - 1)}>Previous rows</button><span>Page {page + 1} / {Math.ceil(view.series.bars.length / 30)}</span><button disabled={(page + 1) * 30 >= view.series.bars.length} onClick={() => setPage(value => value + 1)}>Next rows</button></div></div> : null}
    <details className="provenance"><summary>Source & provenance</summary><dl>
      <dt>Vendor / dataset</dt><dd>{snapshot.vendor} / {snapshot.dataset}</dd><dt>As of</dt><dd>{timestamp(snapshot.as_of)}</dd><dt>Retrieved</dt><dd>{timestamp(snapshot.retrieved_at)}</dd><dt>Source window</dt><dd>{timestamp(snapshot.source_start)} — {timestamp(snapshot.source_end)}</dd><dt>Snapshot</dt><dd className="mono">{snapshot.snapshot_id}</dd><dt>Content hash</dt><dd className="mono">{snapshot.content_hash}</dd>
    </dl><p className="muted">Quality belongs to this saved snapshot, not a live-feed freshness guarantee. Analysis checks freshness again at its selected timestamp.</p></details>
  </>;
}
