import { t, useLocale } from './i18n';
import { useState } from 'react';
import { ApiError, errorMessage, mutate } from './api';
import { instruments, number, percent, priceResponse, timestamp, useResource } from './data';
import type { Instrument, SeriesResponse } from './data';
import StockScreener from './StockScreener';
import { qualityLabel } from './financialLabels';

const groups = ['All assets', 'Stocks', 'ETFs', 'Crypto', 'Index references'] as const;
const groupOf = (item: Instrument) => item.asset_class === 'equity' ? 'Stocks' : item.asset_class === 'etf' ? 'ETFs'
  : item.asset_class === 'crypto' ? 'Crypto' : 'Index references';

export default function Markets() {
  useLocale();
  const [version, setVersion] = useState(0);
  const catalog = useResource<Instrument[]>('/instruments?limit=500', version, instruments);
  const watchlist = useResource<Instrument[]>('/watchlist?limit=200', version, instruments);
  const [group, setGroup] = useState<string>('All assets');
  const [search, setSearch] = useState('');
  const [onlyWatched, setOnlyWatched] = useState(false);
  const [screening, setScreening] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const source = onlyWatched ? watchlist : catalog;
  const visible = (source.data ?? []).filter(item => (group === 'All assets' || groupOf(item) === group)
    && `${item.canonical_symbol} ${item.display_name}`.toLowerCase().includes(search.toLowerCase()));
  const instrument = visible.find(item => item.instrument_id === selected) ?? visible[0];
  const refresh = () => setVersion(value => value + 1);
  return <>
    <div className="market-toolbar">
      <label>{t("Asset group")}<select value={group} onChange={event => setGroup(event.target.value)}>{groups.map(name => <option key={name} value={name}>{t(name)}</option>)}</select></label>
      <label className="search-field">{t("Find an instrument")}<input type="search" value={search} onChange={event => setSearch(event.target.value)} placeholder={t("Symbol or company name")} /></label>
      <label className="checkbox-field"><input type="checkbox" checked={onlyWatched} onChange={event => setOnlyWatched(event.target.checked)} />{t("Watchlist only")}</label>
      <button onClick={refresh}>{t("Reload saved data")}</button>
    </div>
    <p className="muted caption">{t("Saved snapshots · Not a live price feed. Reload reads the database; it does not call a market-data or model provider.")}</p>
    <button onClick={() => setScreening(value => !value)} aria-expanded={screening}>{screening ? t("Close screened candidates") : t("View screened candidates")}</button>
    {screening ? <StockScreener /> : null}
    <div className="market-layout">
      <section className="instrument-list" aria-label={t("Instruments")}>
        <div className="list-heading">{t("Instruments")} <span>{visible.length}</span></div>
        {source.loading ? <p role="status">{t("Loading instruments…")}</p> : source.error ? <p role="alert" className="danger">{t(errorMessage(source.error))}</p>
          : visible.length === 0 ? <p className="muted">{source.data?.length ? t("No instruments match these filters.") : onlyWatched ? t("Your watchlist is empty. Browse all assets to save an instrument.") : t("No instruments have been configured. Import the instrument master before researching markets.")}</p>
          : <ul>{visible.map(item => <li key={item.instrument_id}><button onClick={() => setSelected(item.instrument_id)} aria-pressed={instrument?.instrument_id === item.instrument_id}>
            <span className="instrument-row"><strong>{item.canonical_symbol}</strong><span className="caption">{t(groupOf(item))}</span></span>
            <span className="instrument-name">{item.display_name}</span>
            {item.tradability === 'reference_only' ? <span className="warning caption">{t("Reference only")}</span> : null}
          </button></li>)}</ul>}
        {source.data?.length === (onlyWatched ? 200 : 500) ? <p className="warning">{t("Display limit reached; this list may be incomplete.")}</p> : null}
      </section>
      {instrument ? <InstrumentDetail key={instrument.instrument_id} instrument={instrument} version={version}
        catalog={catalog.data ?? []}
        watched={watchlist.data?.some(item => item.instrument_id === instrument.instrument_id)} watchlistError={watchlist.error}
        onWatchlistChange={refresh} /> : <section className="empty-state"><h2>{t("Select an instrument")}</h2><p>{t("Price history and source details will appear here when saved data is available.")}</p></section>}
    </div>
  </>;
}

function InstrumentDetail({ instrument, catalog, watched, watchlistError, version, onWatchlistChange }: {
  instrument: Instrument; catalog: Instrument[]; watched: boolean | undefined; watchlistError: unknown; version: number; onWatchlistChange: () => void;
}) {
  useLocale();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [cutoff, setCutoff] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [benchmark, setBenchmark] = useState('');
  const [applied, setApplied] = useState('');
  const [queryError, setQueryError] = useState('');
  const [queryVersion, setQueryVersion] = useState(0);
  const series = useResource<SeriesResponse>(`/instruments/${encodeURIComponent(instrument.instrument_id)}/timeseries${applied ? `?${applied}` : ''}`, version + queryVersion, priceResponse);
  function applyWindow(event: React.FormEvent) {
    event.preventDefault();
    if ([cutoff, start, end].some(value => value && (!Number.isFinite(Date.parse(value)) || !/(?:Z|[+-]\d{2}:\d{2})$/i.test(value)))) {
      setQueryError('Use an ISO timestamp with timezone, for example 2026-09-01T00:00:00Z.'); return;
    }
    if (start && end && Date.parse(start) > Date.parse(end)) { setQueryError('Start must not be after end.'); return; }
    const query = new URLSearchParams();
    if (cutoff) query.set('as_of', cutoff);
    if (start) query.set('start', start);
    if (end) query.set('end', end);
    if (benchmark) query.set('benchmark_instrument_id', benchmark);
    setQueryError(''); setApplied(query.toString()); setQueryVersion(value => value + 1);
  }
  async function toggleWatchlist() {
    if (watched === undefined) return;
    setPending(true); setError('');
    try { await mutate(`/watchlist/${encodeURIComponent(instrument.instrument_id)}`, undefined, watched ? 'DELETE' : 'PUT'); onWatchlistChange(); }
    catch (cause) { setError(errorMessage(cause)); }
    finally { setPending(false); }
  }
  return <section className="instrument-detail" aria-label={`${instrument.canonical_symbol} ${t("details")}`}>
    <div className="detail-heading"><div><h2>{instrument.canonical_symbol} <span className="muted">{instrument.display_name}</span></h2>
      <p className="muted caption">{instrument.venue} · {instrument.quote_currency} · {instrument.session_calendar} · {instrument.timezone}</p></div>
      <div className="section-actions"><button onClick={toggleWatchlist} disabled={pending || watched === undefined}>{pending ? t("Saving…") : watched ? t("Remove from watchlist") : t("Add to watchlist")}</button><a className="action-link" href={`#/analysis?instrument=${encodeURIComponent(instrument.instrument_id)}`}>{t("Analyze")}</a></div></div>
    {instrument.tradability === 'reference_only' ? <p className="notice warning">{t("Reference only — context for research, not an investable or executable instrument.")}</p> : null}
    {instrument.asset_class === 'crypto' ? <p className="notice">{t("Crypto · 24/7 market calendar. Separate allocation and policy limits apply.")}</p> : null}
    {error || watchlistError ? <p role="alert" className="danger">{error ? t(error) : `${t("Watchlist unavailable.")} ${t(errorMessage(watchlistError))}`}</p> : null}
    <details className="market-query"><summary>{t("Time window & benchmark")}</summary><form onSubmit={applyWindow}>
      <p className="muted caption">{t("Daily saved prices only. Blank cutoff uses the latest eligible saved snapshot. Dates require an explicit timezone; calculations and benchmark alignment stay on the backend.")}</p>
      <div className="form-grid"><label>{t("Snapshot cutoff (ISO timezone)")}<input value={cutoff} onChange={event => setCutoff(event.target.value)} placeholder={t("Latest available")} /></label>
        <label>{t("Start (ISO timezone)")}<input value={start} onChange={event => setStart(event.target.value)} placeholder={t("All saved history")} /></label>
        <label>{t("End (ISO timezone)")}<input value={end} onChange={event => setEnd(event.target.value)} placeholder={t("Through snapshot")} /></label></div>
      <label>{t("Benchmark")}<select value={benchmark} onChange={event => setBenchmark(event.target.value)}><option value="">{t("No comparison")}</option>{catalog.filter(item => item.instrument_id !== instrument.instrument_id && item.quote_currency === instrument.quote_currency).map(item => <option key={item.instrument_id} value={item.instrument_id}>{item.canonical_symbol}{item.canonical_symbol === instrument.benchmark_symbol ? t(" · configured benchmark") : ''}</option>)}</select></label>
      {queryError ? <p role="alert" className="danger">{t(queryError)}</p> : null}
      <div className="section-actions"><button type="submit">{t("Apply saved-data query")}</button><button type="button" onClick={() => { setCutoff(''); setStart(''); setEnd(''); setBenchmark(''); setApplied(''); setQueryError(''); setQueryVersion(value => value + 1); }}>{t("Reset query")}</button></div>
    </form></details>
    {series.loading ? <p role="status">{t("Loading saved price history…")}</p> : series.error ? <div className="empty-state" role="status"><h2>{t("Price history unavailable")}</h2><p>{series.error instanceof ApiError && series.error.status === 404 ? t("No owner-readable price snapshot is available for the asset or benchmark at this cutoff. Ingest market data before analysis; no substitute prices are shown.") : series.error instanceof ApiError && series.error.status === 422 ? t("The requested window or comparison is unavailable. Check dates, matching currency/interval and at least two aligned observations; no substitute comparison is shown.") : t(errorMessage(series.error))}</p></div>
      : series.data ? <PriceHistory key={applied} data={series.data} catalog={catalog} /> : null}
  </section>;
}

function PriceHistory({ data, catalog }: { data: SeriesResponse; catalog: Instrument[] }) {
  useLocale();
  const { snapshot, view } = data;
  const [showTable, setShowTable] = useState(false);
  const [page, setPage] = useState(0);
  const points = view.returns;
  // Chart geometry only. Returns, drawdown and volatility come from the backend.
  const valid = Array.isArray(points) && points.length > 0 && points.every(point => Number.isFinite(point.price) && Number.isFinite(Date.parse(point.timestamp)));
  if (!valid) return <p role="alert" className="danger">{t("Price response is invalid; chart withheld.")}</p>;
  const prices = points.map(point => point.price);
  const minimum = prices.reduce((value, price) => Math.min(value, price), Infinity);
  const maximum = prices.reduce((value, price) => Math.max(value, price), -Infinity);
  const start = Date.parse(points[0].timestamp);
  const duration = Date.parse(points[points.length - 1].timestamp) - start || 1;
  const range = maximum - minimum || maximum * .02 || 1;
  const polyline = points.map(point => `${50 + (Date.parse(point.timestamp) - start) / duration * 820},${230 - (point.price - minimum) / range * 180}`).join(' ');
  const rows = view.series.bars.slice(page * 30, (page + 1) * 30);
  return <>
    <div className="quality-line"><span className={snapshot.quality_status === 'OK' ? 'muted' : 'warning'}>{t("Snapshot quality:")} {qualityLabel(snapshot.quality_status)}</span><span>{snapshot.vendor.startsWith('yfinance.') ? 'Yahoo Finance' : snapshot.vendor}</span><span>{t("Source through")} {timestamp(snapshot.source_end)}</span></div>
    {snapshot.metadata?.freshness === 'delayed' ? <p className="notice warning">{t('The source is delayed. These are the latest verified saved candles, not a current-market quote.')}</p> : null}
    {snapshot.quality_reasons.length ? <p className="notice warning">{snapshot.quality_reasons.join(' · ')}</p> : null}
    <div className="metrics">
      <div><span>{t("Last saved price ·")} {view.series.quote_currency}</span><strong>{number(points[points.length - 1].price)}</strong></div>
      <div><span>{t("Period return")}</span><strong>{percent(view.statistics.total_return)}</strong></div>
      <div><span>{t("Annualized volatility")}</span><strong>{percent(view.statistics.annualized_volatility)}</strong></div>
      <div><span>{t("Maximum drawdown")}</span><strong>{percent(view.statistics.maximum_drawdown)}</strong></div>
    </div>
    <figure className="price-chart"><svg viewBox="0 0 900 280" role="img" aria-label={`${t("Saved")} ${view.statistics.price_basis} ${t("history in")} ${view.series.quote_currency}; ${points.length} ${t("observations. Data table available below.")}`}>
      <line x1="50" x2="870" y1="230" y2="230" stroke="var(--border)" /><line x1="50" x2="870" y1="50" y2="50" stroke="var(--border)" />
      <text x="50" y="36">{number(maximum)} {view.series.quote_currency}</text><text x="50" y="252">{number(minimum)}</text>
      <polyline points={polyline} fill="none" stroke="var(--accent)" strokeWidth="2" vectorEffect="non-scaling-stroke" />
      {points.length === 1 ? <circle cx="50" cy="230" r="4" fill="var(--accent)" /> : null}
    </svg><figcaption>{timestamp(points[0].timestamp)} — {timestamp(points[points.length - 1].timestamp)}<br />{t(view.statistics.price_basis === 'adjusted_close' ? 'Adjusted close' : 'Close')} · {view.series.interval} · {view.statistics.observations}  {t("observations")}</figcaption></figure>
    <button onClick={() => setShowTable(value => !value)} aria-expanded={showTable} aria-controls="price-table">{showTable ? t("Hide price table") : t("Show price table")}</button>
    {showTable ? <div id="price-table"><div className="table-scroll" role="region" aria-label={t("Saved OHLCV price history")} tabIndex={0}><table><caption>{t("Saved OHLCV ·")} {view.series.quote_currency}  {t("· UTC timestamps")}</caption><thead><tr>{['Session date', 'Candle closed at (UTC)', 'Open', 'High', 'Low', 'Close', 'Adjusted close', 'Volume'].map(label => <th key={label} scope="col">{t(label)}</th>)}</tr></thead><tbody>{rows.map(bar => <tr key={bar.timestamp}><th scope="row">{bar.session_date ?? t('Unavailable')}</th><td>{timestamp(bar.timestamp)}</td>{[bar.open, bar.high, bar.low, bar.close, bar.adjusted_close, bar.volume].map((value, index) => <td key={index}>{value === null ? t("Unavailable") : number(value, index === 5 ? 0 : 2)}</td>)}</tr>)}</tbody></table></div>
      <div className="pagination"><button disabled={page === 0} onClick={() => setPage(value => value - 1)}>{t("Previous rows")}</button><span>{t("Page")} {page + 1} / {Math.ceil(view.series.bars.length / 30)}</span><button disabled={(page + 1) * 30 >= view.series.bars.length} onClick={() => setPage(value => value + 1)}>{t("Next rows")}</button></div></div> : null}
    <details className="provenance"><summary>{t("Source & provenance")}</summary><dl>
      <dt>{t("Vendor / dataset")}</dt><dd>{snapshot.vendor} / {snapshot.dataset}</dd><dt>{t("As of")}</dt><dd>{timestamp(snapshot.as_of)}</dd><dt>{t("Retrieved")}</dt><dd>{timestamp(snapshot.retrieved_at)}</dd><dt>{t("Source window")}</dt><dd>{timestamp(snapshot.source_start)} — {timestamp(snapshot.source_end)}</dd><dt>{t("Snapshot")}</dt><dd className="mono">{snapshot.snapshot_id}</dd><dt>{t("Content hash")}</dt><dd className="mono">{snapshot.content_hash}</dd>
    </dl><p className="muted">{t("Quality belongs to this saved snapshot, not a live-feed freshness guarantee. Analysis checks freshness again at its selected timestamp.")}</p></details>
    {view.benchmark ? <section className="benchmark-panel" aria-label={t("Saved benchmark comparison")}><h3>{t("Benchmark ·")} {catalog.find(item => item.instrument_id === view.benchmark!.benchmark_instrument_id)?.canonical_symbol ?? view.benchmark.benchmark_instrument_id}</h3>
      {!data.benchmark_snapshot ? <p className="warning">{t("Benchmark provenance unavailable; comparison withheld.")}</p> : <>
        <p className="muted">{view.benchmark.aligned_observations}  {t("aligned observations ·")} {data.benchmark_snapshot.vendor}  {t("· Quality")} {data.benchmark_snapshot.quality_status}</p>
        {data.benchmark_snapshot.quality_status !== 'OK' ? <p className="warning">{t("Benchmark is not quality-OK. These are saved descriptive metrics, not an eligible investment conclusion.")}</p> : null}
        <dl><dt>{t("Asset aligned return")}</dt><dd>{percent(view.benchmark.asset_return)}</dd><dt>{t("Benchmark return")}</dt><dd>{percent(view.benchmark.benchmark_return)}</dd><dt>{t("Excess return")}</dt><dd>{percent(view.benchmark.excess_return)}</dd><dt>{t("Correlation")}</dt><dd>{view.benchmark.correlation === null ? t("Unavailable") : number(view.benchmark.correlation, 4)}</dd><dt>{t("Tracking error (annualized)")}</dt><dd>{percent(view.benchmark.annualized_tracking_error)}</dd></dl>
        <details><summary>{t("Benchmark provenance")}</summary><dl><dt>{t("Snapshot")}</dt><dd className="mono">{data.benchmark_snapshot.snapshot_id}</dd><dt>{t("As of")}</dt><dd>{timestamp(data.benchmark_snapshot.as_of)}</dd><dt>{t("Retrieved")}</dt><dd>{timestamp(data.benchmark_snapshot.retrieved_at)}</dd><dt>{t("Source through")}</dt><dd>{timestamp(data.benchmark_snapshot.source_end)}</dd><dt>{t("Hash")}</dt><dd className="mono">{data.benchmark_snapshot.content_hash}</dd></dl></details>
      </>}
    </section> : null}
  </>;
}
