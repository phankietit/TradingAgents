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
  expect(await screen.findByText('Snapshot quality: STALE')).toBeTruthy();
  expect(screen.getByText('1.94%')).toBeTruthy();
  expect(screen.getByRole('img').getAttribute('aria-label')).toContain('2 observations');
  await user.click(screen.getByRole('button', { name: 'Show price table' }));
  expect(screen.getByRole('table')).toBeTruthy();
  expect(screen.getAllByText('Unavailable').length).toBe(2);
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
