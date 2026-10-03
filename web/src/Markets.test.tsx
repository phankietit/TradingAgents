import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import Markets from './Markets';

const apple = { instrument_id: 'apple-id', canonical_symbol: 'AAPL', display_name: 'Apple Inc.', asset_class: 'equity',
  tradability: 'investable', venue: 'NASDAQ', quote_currency: 'USD', timezone: 'America/New_York', session_calendar: 'XNYS', benchmark_symbol: 'SPY' };
const reference = { ...apple, instrument_id: 'nq-id', canonical_symbol: 'NQ', display_name: 'Nasdaq futures reference', asset_class: 'reference_future', tradability: 'reference_only' };
const saved = {
  snapshot: { snapshot_id: 'snapshot-fixture', dataset: 'ohlcv.daily', vendor: 'TEST FIXTURE', as_of: '2026-09-23T12:00:00Z', retrieved_at: '2026-09-23T12:00:00Z', source_start: '2026-09-21T20:00:00Z', source_end: '2026-09-22T20:00:00Z', content_hash: 'sha256:fixture', quality_status: 'STALE', quality_reasons: ['Fixture source is stale'] },
  view: { series: { instrument_id: 'apple-id', interval: '1d', quote_currency: 'USD', timezone: 'America/New_York', bars: [
    { timestamp: '2026-09-21T20:00:00Z', open: 100, high: 104, low: 99, close: 103, adjusted_close: null, volume: 1000 },
    { timestamp: '2026-09-22T20:00:00Z', open: 103, high: 106, low: 101, close: 105, adjusted_close: null, volume: 1200 },
  ] }, returns: [{ timestamp: '2026-09-21T20:00:00Z', price: 103, simple_return: null, drawdown: 0 }, { timestamp: '2026-09-22T20:00:00Z', price: 105, simple_return: .0194, drawdown: 0 }], statistics: { observations: 2, price_basis: 'close', total_return: .0194, annualized_volatility: .12, maximum_drawdown: 0 } },
};
afterEach(() => vi.unstubAllGlobals());

function setup(missing = false) {
  let watched = false;
  const fetch = vi.fn(async (url: string, init: RequestInit) => {
    if (url.includes('/auth/csrf')) return new Response(JSON.stringify({ csrf_token: 'fixture-csrf' }));
    if (url.endsWith('/watchlist/apple-id')) { watched = init.method === 'PUT'; return new Response(JSON.stringify({ status: 'saved' })); }
    if (url.includes('/watchlist?')) return new Response(JSON.stringify(watched ? [apple] : []));
    if (url.includes('/timeseries')) return new Response(JSON.stringify(saved), { status: missing || url.includes('nq-id') ? 404 : 200 });
    return new Response(JSON.stringify([apple, reference]));
  });
  vi.stubGlobal('fetch', fetch); return fetch;
}

it('renders backend metrics, stale provenance, chart and accessible table', async () => {
  setup(); const user = userEvent.setup(); render(<Markets />);
  expect(await screen.findByText('Snapshot quality: Outdated data')).toBeTruthy();
  expect(screen.getByText('1.94%')).toBeTruthy();
  expect(screen.getByRole('img').getAttribute('aria-label')).toContain('2 observations');
  await user.click(screen.getByRole('button', { name: 'Show price table' }));
  expect(screen.getByRole('table')).toBeTruthy();
  expect(screen.getByRole('columnheader', {name:'Session date'})).toBeTruthy();
  expect(screen.getByRole('columnheader', {name:'Candle closed at (UTC)'})).toBeTruthy();
  // Legacy fixtures have neither explicit session labels nor adjusted closes.
  expect(screen.getAllByText('Unavailable').length).toBe(4);
  await user.click(screen.getByText('Source & provenance'));
  expect(screen.getByText('TEST FIXTURE / ohlcv.daily')).toBeTruthy();
});

it('saves watchlist through CSRF and filters the server result', async () => {
  const fetch = setup(); const user = userEvent.setup(); render(<Markets />);
  await user.click(await screen.findByRole('button', { name: 'Add to watchlist' }));
  expect(await screen.findByRole('button', { name: 'Remove from watchlist' })).toBeTruthy();
  expect(fetch.mock.calls.some(([url, init]) => url.endsWith('/watchlist/apple-id') && init.method === 'PUT')).toBe(true);
  await user.click(screen.getByLabelText('Watchlist only'));
  expect(screen.queryByRole('button', { name: /NQ/ })).toBeNull();
});

it('withholds missing prices and identifies reference-only instruments', async () => {
  setup(true); const user = userEvent.setup(); render(<Markets />);
  expect(await screen.findByText('Price history unavailable')).toBeTruthy();
  expect(screen.queryByRole('img')).toBeNull();
  await user.selectOptions(screen.getByLabelText('Asset group'), 'Index references');
  expect(await screen.findByText(/context for research, not an investable/)).toBeTruthy();
  expect(screen.queryByRole('button', { name: /AAPL/ })).toBeNull();
});

it('sends an explicit time window and benchmark to the backend without local recomputation', async () => {
  const fetch = setup(); const user = userEvent.setup(); render(<Markets />);
  await screen.findByText('Snapshot quality: Outdated data');
  await user.click(screen.getByText('Time window & benchmark'));
  await user.type(screen.getByLabelText('Snapshot cutoff (ISO timezone)'), '2026-09-23T12:00:00Z');
  await user.type(screen.getByLabelText('Start (ISO timezone)'), '2026-09-20T00:00:00Z');
  await user.type(screen.getByLabelText('End (ISO timezone)'), '2026-09-23T00:00:00Z');
  await user.selectOptions(screen.getByLabelText('Benchmark'), 'nq-id');
  await user.click(screen.getByRole('button', {name:'Apply saved-data query'}));
  expect(fetch.mock.calls.some(([url]) => url.includes('benchmark_instrument_id=nq-id') && url.includes('as_of=2026-09-23T12%3A00%3A00Z') && url.includes('start=2026-09-20T00%3A00%3A00Z'))).toBe(true);
  await user.click(screen.getByRole('button', {name:'Reset query'}));
  expect((screen.getByLabelText('Start (ISO timezone)') as HTMLInputElement).value).toBe('');
});

it('rejects timestamps without timezone before requesting a different price window', async () => {
  const fetch = setup(); const user = userEvent.setup(); render(<Markets />);
  await screen.findByText('Snapshot quality: Outdated data');
  await user.click(screen.getByText('Time window & benchmark'));
  await user.type(screen.getByLabelText('Start (ISO timezone)'), '2026-09-20T00:00:00');
  await user.click(screen.getByRole('button', {name:'Apply saved-data query'}));
  expect(screen.getByRole('alert').textContent).toContain('ISO timestamp with timezone');
  expect(fetch.mock.calls.some(([url]) => url.includes('start='))).toBe(false);
});

it('shows backend comparison metrics only when benchmark provenance is present', async () => {
  const response = { ...saved, benchmark_snapshot: saved.snapshot, view: { ...saved.view,
    benchmark: { benchmark_instrument_id: 'nq-id', aligned_observations: 2, asset_return: .01,
      benchmark_return: .02, excess_return: -.01, correlation: null, annualized_tracking_error: .03 } } };
  vi.stubGlobal('fetch', vi.fn(async (url: string) => new Response(JSON.stringify(url.includes('/timeseries') ? response : url.includes('/watchlist?') ? [] : [apple, reference]))));
  render(<Markets />);
  expect(await screen.findByRole('region', {name:'Saved benchmark comparison'})).toBeTruthy();
  expect(screen.getByText('-1.00%')).toBeTruthy();
  expect(screen.getByText(/Benchmark is not quality-OK/)).toBeTruthy();
});

it('withholds malformed price payloads without a blank page or synthetic metrics', async () => {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => new Response(JSON.stringify(url.includes('/timeseries') ? { snapshot: null, view: {} } : url.includes('/watchlist?') ? [] : [apple]))));
  render(<Markets />);
  expect(await screen.findByText('Price history unavailable')).toBeTruthy();
  expect(screen.queryByRole('img')).toBeNull();
  expect(screen.queryByText('0.00%')).toBeNull();
});

it('does not show benchmark metrics when the comparison has no source manifest', async () => {
  const response = { ...saved, view: { ...saved.view, benchmark: { benchmark_instrument_id: 'nq-id',
    aligned_observations: 2, asset_return: .01, benchmark_return: .02, excess_return: -.01,
    correlation: null, annualized_tracking_error: .03 } } };
  vi.stubGlobal('fetch', vi.fn(async (url: string) => new Response(JSON.stringify(url.includes('/timeseries') ? response : url.includes('/watchlist?') ? [] : [apple, reference]))));
  render(<Markets />);
  expect(await screen.findByText('Benchmark provenance unavailable; comparison withheld.')).toBeTruthy();
  expect(screen.queryByText('-1.00%')).toBeNull();
});
