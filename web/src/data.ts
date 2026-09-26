import { useEffect, useState } from 'react';
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
}
export interface SeriesResponse {
  snapshot: Snapshot;
  view: {
    series: { instrument_id: string; interval: string; quote_currency: string; timezone: string; bars: {
      timestamp: string; open: number; high: number; low: number; close: number;
      adjusted_close: number | null; volume: number;
    }[] };
    returns: { timestamp: string; price: number; simple_return: number | null; drawdown: number }[];
    statistics: { observations: number; price_basis: string; total_return: number;
      annualized_volatility: number; maximum_drawdown: number };
  };
}

export function instruments(value: Instrument[]): Instrument[] {
  if (!Array.isArray(value) || value.some(item => !item ||
    ['instrument_id', 'canonical_symbol', 'display_name', 'asset_class', 'tradability', 'venue', 'quote_currency', 'timezone', 'session_calendar']
      .some(key => typeof item[key as keyof Instrument] !== 'string'))) throw new ApiError(502);
  return value;
}

type Resource<T> = { path: string | null; data?: T; error?: unknown; loading: boolean };
/** Path-tagged state prevents even one paint of a previous instrument's values. */
export function useResource<T>(path: string | null, version = 0, validate?: (value: T) => T) {
  const [state, setState] = useState<Resource<T>>({ path, loading: !!path });
  useEffect(() => {
    if (!path) return;
    const controller = new AbortController();
    setState({ path, loading: true });
    request<T>(path, { signal: controller.signal }).then(value => validate ? validate(value) : value)
      .then(data => { if (!controller.signal.aborted) setState({ path, data, loading: false }); })
      .catch(error => { if (!controller.signal.aborted) setState({ path, error, loading: false }); });
    return () => controller.abort();
  }, [path, version, validate]);
  return state.path === path ? state : { path, loading: !!path } as Resource<T>;
}

export function number(value: number, digits = 2): string {
  return Number.isFinite(value) ? value.toLocaleString('en-US', { maximumFractionDigits: digits, minimumFractionDigits: digits }) : 'Unavailable';
}
export const percent = (value: number) => Number.isFinite(value) ? `${number(value * 100)}%` : 'Unavailable';
export function timestamp(value: string | null): string {
  if (!value) return 'Unavailable';
  const date = new Date(value);
  return Number.isFinite(date.getTime()) ? date.toISOString().replace('T', ' ').replace('.000Z', ' UTC') : 'Invalid timestamp';
}
