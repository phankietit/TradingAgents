import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import StockScreener from './StockScreener';

afterEach(() => vi.unstubAllGlobals());
const saved = { screening_snapshot_id: 'screening-fixture', as_of: '2026-09-01T00:00:00Z', generated_at: '2026-09-01T00:00:00Z',
  input_count: 2, input_hash: 'sha256:fixture-input', universe_hash: 'sha256:fixture-universe',
  policy: {policy_id:'SYNTHETIC POLICY', schema_version:'1.0', min_history_days:252},
  candidates: [{rank:1,instrument_id:'aapl',canonical_symbol:'AAPL',source_snapshot_id:'source-fixture',market_cap_usd:100_000_000_000,
    average_dollar_volume_20d_usd:100_000_000,annualized_volatility:.3,ranking_score:2,market_cap_rank:1,liquidity_rank:1}],
  exclusions: [{instrument_id:'excluded',canonical_symbol:'EXCLUDED',codes:['history'],reasons:['<script>missing history</script>']}],
};
const history = [{artifact_id: saved.screening_snapshot_id, created_at: saved.generated_at}];
function setup(data: unknown = saved, list: unknown = history, status = 200) {
  const fetch = vi.fn(async (url: string) => new Response(JSON.stringify(url.includes('?') ? list : data), {status:url.includes('?') ? 200 : status}));
  vi.stubGlobal('fetch', fetch); return fetch;
}

it('renders backend ranks, policy, source IDs and explicit exclusions without ranking or enqueue side effects', async () => {
  const fetch = setup(); const user = userEvent.setup(); render(<StockScreener />);
  expect(await screen.findByText('1 · AAPL')).toBeTruthy();
  expect(screen.getByText('100,000,000,000')).toBeTruthy();
  expect(screen.getByText('source-fixture')).toBeTruthy();
  expect(screen.getByRole('link',{name:'Configure research'}).getAttribute('href')).toBe('#/analysis?instrument=aapl');
  await user.click(screen.getByRole('button',{name:'Excluded (1)'}));
  expect(screen.getByText('history: <script>missing history</script>')).toBeTruthy();
  expect(document.querySelector('script')).toBeNull();
  await user.click(screen.getByText('Screening policy & provenance'));
  expect(screen.getByText('sha256:fixture-input')).toBeTruthy();
  expect(fetch.mock.calls.every(([url]) => url.startsWith('/api/v1/screenings'))).toBe(true);
});

it('distinguishes missing screening data from a valid empty candidate universe', async () => {
  setup(saved, []); const view = render(<StockScreener />);
  expect(await screen.findByText(/No owner screening snapshots/)).toBeTruthy();
  view.unmount();
  setup({...saved,input_count:1,candidates:[]}); render(<StockScreener />);
  expect(await screen.findByText(/No equities met this saved policy/)).toBeTruthy();
  expect(screen.queryByText(/No owner screening snapshots/)).toBeNull();
});

it.each(['wrong_id','malformed','integrity_failure'] as const)('withholds candidates for %s', async reason => {
  setup(reason === 'malformed' ? {} : reason === 'wrong_id' ? {...saved,screening_snapshot_id:'other-id'} : saved, history, reason === 'integrity_failure' ? 409 : 200);
  render(<StockScreener />);
  expect((await screen.findByRole('alert')).textContent).toContain('No eligible universe is implied');
  expect(screen.queryByRole('link',{name:'Configure research'})).toBeNull();
});

it('fails safely when history metadata is malformed', async () => {
  setup(saved, {unexpected:'value'}); render(<StockScreener />);
  expect(await screen.findByRole('alert')).toBeTruthy();
  expect(screen.queryByRole('table')).toBeNull();
});
