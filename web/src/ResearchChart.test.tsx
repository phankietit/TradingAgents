import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it } from 'vitest';
import ResearchChart, { reportHistories } from './ResearchChart';

const history = { snapshot_id: 'immutable-fixture', quote_currency: 'USD', price_basis: 'close', points: [
  { closed_at: '2026-01-02T00:00:00Z', session_date: '2026-01-01', price: 100 },
  { closed_at: '2026-09-20T00:00:00Z', session_date: '2026-09-19', price: 120 },
] };
it('switches the chart window and inspects saved candles without provider calls', async () => {
  const user = userEvent.setup(); render(<ResearchChart history={history} />);
  expect(screen.getByText('120.00')).toBeTruthy();
  expect(screen.getByText('2026-09-19')).toBeTruthy();
  await user.click(screen.getByRole('button', { name: '1M' }));
  expect(screen.getByRole('slider').getAttribute('max')).toBe('0');
  await user.click(screen.getByRole('button', { name: 'All' }));
  expect(screen.getByRole('slider').getAttribute('max')).toBe('1');
  expect(screen.getByRole('img').getAttribute('aria-labelledby')).toBeTruthy();
});
it('withholds malformed, future-ordered or nonfinite chart payloads and supports legacy absence', () => {
  expect(reportHistories(undefined)).toEqual([]);
  expect(reportHistories([history])).toHaveLength(1);
  expect(() => reportHistories([{ ...history, points: [...history.points].reverse() }])).toThrow();
  expect(() => reportHistories([{ ...history, points: [{ ...history.points[0], price: NaN }] }])).toThrow();
});
