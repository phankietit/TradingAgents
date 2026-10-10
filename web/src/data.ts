import { t, formatLocale } from './i18n';
import { useEffect, useRef, useState } from 'react';
import { ApiError, request } from './api';

export interface Instrument {
  instrument_id: string; canonical_symbol: string; display_name: string;
  asset_class: string; tradability: string; venue: string; quote_currency: string;
  timezone: string; session_calendar: string; benchmark_symbol: string | null;
}
export interface Snapshot {
  snapshot_id: string; dataset: string; vendor: string; as_of: string; retrieved_at: string;
  source_start: string | null; source_end: string | null; content_hash: string;
  quality_status: string; quality_reasons: string[];
  metadata?: { freshness?: string; missing_trailing_sessions?: number; data_through?: string;
    series_id?: string; units?: string; frequency_short?: string; vintage_date?: string;
    last_observation_date?: string | null; observation_start?: string; observation_end?: string;
    posts?: number; received_posts?: number | null; coverage?: string };
}
export interface SeriesResponse {
  snapshot: Snapshot;
  benchmark_snapshot?: Snapshot | null;
  view: {
    series: { instrument_id: string; interval: string; quote_currency: string; timezone: string; bars: {
      timestamp: string; session_date?: string | null; open: number; high: number; low: number; close: number;
      adjusted_close: number | null; volume: number;
    }[] };
    returns: { timestamp: string; price: number; simple_return: number | null; drawdown: number }[];
    statistics: { observations: number; price_basis: string; total_return: number;
      annualized_volatility: number; maximum_drawdown: number };
    benchmark?: { benchmark_instrument_id: string; aligned_observations: number; asset_return: number;
      benchmark_return: number; excess_return: number; correlation: number | null; annualized_tracking_error: number } | null;
  };
}

export function instruments(value: Instrument[]): Instrument[] {
  if (!Array.isArray(value) || value.some(item => !item ||
    ['instrument_id', 'canonical_symbol', 'display_name', 'asset_class', 'tradability', 'venue', 'quote_currency', 'timezone', 'session_calendar']
      .some(key => typeof item[key as keyof Instrument] !== 'string'))) throw new ApiError(502);
  return value;
}

/** Validate display shape before rendering; all financial computations stay server-side. */
export function priceResponse(value: SeriesResponse): SeriesResponse {
  const string = (item: unknown) => typeof item === 'string';
  const strings = (items: unknown) => Array.isArray(items) && items.every(string);
  const date = (item: unknown) => string(item) && Number.isFinite(Date.parse(item as string));
  const snapshot = (item: Snapshot) => item &&
    [item.snapshot_id, item.dataset, item.vendor, item.content_hash, item.quality_status].every(string) &&
    date(item.as_of) && date(item.retrieved_at) && strings(item.quality_reasons) &&
    (item.source_start === null || date(item.source_start)) && (item.source_end === null || date(item.source_end));
  try {
    const { view } = value;
    const benchmark = view.benchmark;
    const valid = snapshot(value.snapshot) && view.series &&
      [view.series.instrument_id, view.series.interval, view.series.quote_currency, view.series.timezone].every(string) &&
      Array.isArray(view.series.bars) && view.series.bars.length > 0 && view.series.bars.every(bar => bar && date(bar.timestamp) &&
        (bar.session_date == null || (string(bar.session_date) && /^\d{4}-\d{2}-\d{2}$/.test(bar.session_date))) &&
        [bar.open, bar.high, bar.low, bar.close, bar.volume].every(Number.isFinite) && (bar.adjusted_close === null || Number.isFinite(bar.adjusted_close))) &&
      Array.isArray(view.returns) && view.returns.length > 0 && view.returns.every(point => point && date(point.timestamp) &&
        [point.price, point.drawdown].every(Number.isFinite) && (point.simple_return === null || Number.isFinite(point.simple_return))) &&
      view.statistics && string(view.statistics.price_basis) && Number.isInteger(view.statistics.observations) &&
      [view.statistics.total_return, view.statistics.annualized_volatility, view.statistics.maximum_drawdown].every(Number.isFinite) &&
      (!benchmark || (string(benchmark.benchmark_instrument_id) && Number.isInteger(benchmark.aligned_observations) &&
        [benchmark.asset_return, benchmark.benchmark_return, benchmark.excess_return, benchmark.annualized_tracking_error].every(Number.isFinite) &&
        (benchmark.correlation === null || Number.isFinite(benchmark.correlation)))) &&
      (!value.benchmark_snapshot || snapshot(value.benchmark_snapshot));
    if (!valid) throw new ApiError(502);
  } catch { throw new ApiError(502); }
  return value;
}

type Resource<T> = { path: string | null; data?: T; error?: unknown; loading: boolean };
/** Path-tagged state prevents even one paint of a previous instrument's values. */
export function useResource<T>(path: string | null, version = 0, validate?: (value: T) => T, retainWhileRefreshing = false) {
  const [state, setState] = useState<Resource<T>>({ path, loading: !!path });
  const refresh = useRef<(() => void) | null>(null);
  // Default consumers still cancel/clear on every version change. Only read-only
  // polling keeps the request scope stable across ticks, avoiding starvation.
  const resetVersion = retainWhileRefreshing ? 0 : version;
  useEffect(() => {
    if (!path) return;
    const controller = new AbortController();
    let reading = false;
    let again = false;
    const read = async () => {
      if (reading) { again = true; return; }
      reading = true;
      do {
        again = false;
        setState(previous => retainWhileRefreshing && previous.path === path && previous.data !== undefined
          ? {path, data: previous.data, loading: false} : { path, loading: true });
        try {
          const value = await request<T>(path, {signal:controller.signal});
          const data = validate ? validate(value) : value;
          if (controller.signal.aborted) return;
          setState({path, data, loading:false});
        } catch (error) {
          if (controller.signal.aborted) return;
          setState({path, error, loading:false});
        }
      } while (again && !controller.signal.aborted);
      reading = false;
    };
    refresh.current = read;
    return () => { controller.abort(); refresh.current = null; };
  }, [path, resetVersion, validate, retainWhileRefreshing]);
  useEffect(() => { refresh.current?.(); }, [path, version, validate, retainWhileRefreshing]);
  return state.path === path ? state : { path, loading: !!path } as Resource<T>;
}

export function number(value: number, digits = 2): string {
  return Number.isFinite(value) ? value.toLocaleString(formatLocale(), { maximumFractionDigits: digits, minimumFractionDigits: digits }) : t('Unavailable');
}
export const percent = (value: number) => Number.isFinite(value) ? `${number(value * 100)}%` : t('Unavailable');
export function timestamp(value: string | null): string {
  if (!value) return t('Unavailable');
  const date = new Date(value);
  return Number.isFinite(date.getTime()) ? date.toISOString().replace('T', ' ').replace(/(?:\.000)?Z$/, ' UTC') : t('Invalid timestamp');
}
