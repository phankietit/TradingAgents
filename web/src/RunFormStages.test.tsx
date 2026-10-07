import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import RunForm from './RunForm';

const catalog = [{ instrument_id: 'aapl', canonical_symbol: 'AAPL', display_name: 'Apple',
  asset_class: 'equity', tradability: 'investable', venue: 'NASDAQ', quote_currency: 'USD',
  timezone: 'America/New_York', session_calendar: 'XNAS', benchmark_symbol: 'SPY' }];
const source = { snapshot: { snapshot_id: 'source1', dataset: 'ohlcv.daily', vendor: 'TEST FIXTURE',
  source_end: '2026-09-01T00:00:00Z', quality_status: 'OK' }, metadata_eligible: true,
  ineligibility_reasons: [], supported_analysts: ['market'] };
function setup() {
  const fetch = vi.fn(async (url: string) => new Response(JSON.stringify(
    url.includes('/analysis-profile') ? { allowed_analysts: ['market', 'news'], investable: true }
      : url.includes('/snapshots?') ? [source] : url.endsWith('/auth/csrf') ? { csrf_token: 'synthetic' }
        : url.endsWith('/runs') ? { run: { run_id: 'synthetic-run' } } : [])));
  vi.stubGlobal('fetch', fetch);
  return fetch;
}
afterEach(() => vi.unstubAllGlobals());

it('shows one stage, preserves scope and sources, and navigation never starts AI', async () => {
  const fetch = setup(); const user = userEvent.setup();
  render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={vi.fn()} />);
  expect(screen.getByRole('region', { name: 'Research scope' })).toBeTruthy();
  expect(screen.queryByRole('region', { name: 'Prepare market data' })).toBeNull();
  expect(screen.queryByRole('checkbox', { name: /I authorize/ })).toBeNull();
  await user.selectOptions(screen.getByLabelText('Report language'), 'vi');
  await user.click(screen.getByRole('button', { name: 'Continue to data' }));
  const data = screen.getByRole('region', { name: 'Prepare market data' });
  expect(document.activeElement).toBe(data);
  expect(screen.queryByRole('region', { name: 'Research scope' })).toBeNull();
  await user.click(screen.getByRole('button', { name: 'Choose saved sources' }));
  const group = await screen.findByRole('group', { name: 'Price & trend' });
  await user.click(within(group).getByRole('checkbox'));
  await user.click(screen.getByRole('button', { name: 'Continue to review' }));
  const review = screen.getByRole('region', { name: 'Analysis request summary' });
  expect(document.activeElement).toBe(review);
  expect(within(review).getByText('Vietnamese')).toBeTruthy();
  expect(within(review).getByText(/TEST FIXTURE/)).toBeTruthy();
  expect(within(review).getByText('Not included')).toBeTruthy();
  await user.click(screen.getByRole('button', { name: 'Back to data' }));
  expect((within(group).getByRole('checkbox') as HTMLInputElement).checked).toBe(true);
  await user.click(screen.getByRole('button', { name: 'Back to scope' }));
  expect((screen.getByLabelText('Report language') as HTMLSelectElement).value).toBe('vi');
  expect(fetch.mock.calls.some(([url]) => url.endsWith('/runs') || /\/prepare-/.test(url))).toBe(false);
});

it('requires unchanged explicit consent at review and refuses submit from another stage', async () => {
  const fetch = setup(); const user = userEvent.setup(); const created = vi.fn();
  render(<RunForm catalog={catalog} onClose={vi.fn()} onCreated={created} />);
  await user.click(screen.getByRole('button', { name: 'Continue to data' }));
  await user.click(screen.getByRole('button', { name: 'Choose saved sources' }));
  await user.click(within(await screen.findByRole('group', { name: 'Price & trend' })).getByRole('checkbox'));
  await user.click(screen.getByRole('button', { name: 'Continue to review' }));
  expect((screen.getByRole('button', { name: 'Queue analysis' }) as HTMLButtonElement).disabled).toBe(true);
  await user.click(screen.getByRole('checkbox', { name: /I authorize/ }));
  await user.click(screen.getByRole('button', { name: 'Research scope' }));
  fireEvent.submit(screen.getByRole('form', { name: 'New analysis' }));
  expect(fetch.mock.calls.some(([url]) => url.endsWith('/runs'))).toBe(false);
  await user.selectOptions(screen.getByLabelText('Report language'), 'vi');
  await user.click(screen.getByRole('button', { name: 'Review & authorize' }));
  expect((screen.getByRole('checkbox', { name: /I authorize/ }) as HTMLInputElement).checked).toBe(false);
  expect((screen.getByRole('button', { name: 'Queue analysis' }) as HTMLButtonElement).disabled).toBe(true);
  await user.click(screen.getByRole('checkbox', { name: /I authorize/ }));
  await user.click(screen.getByRole('button', { name: 'Queue analysis' }));
  await waitFor(() => expect(created).toHaveBeenCalledTimes(1));
  expect(fetch.mock.calls.filter(([url]) => url.endsWith('/runs'))).toHaveLength(1);
});
