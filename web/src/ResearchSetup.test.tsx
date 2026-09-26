import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import ResearchSetup from './ResearchSetup';

afterEach(() => vi.unstubAllGlobals());
const config = { provider:'fixture',quick_model:'quick-fixture',deep_model:'deep-fixture',worker_status:'UNVERIFIED',provider_connection:'UNVERIFIED',max_job_attempts:3 };
it('shows uncertainty and opens model details without a probe or mutation', async () => {
  const fetch = vi.fn(async () => new Response(JSON.stringify(config)));
  vi.stubGlobal('fetch',fetch); render(<ResearchSetup />);
  expect(await screen.findByText(/No paid connection test/)).toBeTruthy();
  const model = screen.getByText('quick-fixture');
  expect(model.closest('details')?.open).toBe(false);
  await userEvent.click(screen.getByText('Models & processing details'));
  expect(model.closest('details')?.open).toBe(true);
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(fetch).toHaveBeenCalledWith('/api/v1/analysis-configuration', expect.any(Object));
});
it.each([{}, {...config,worker_status:'READY'}])('does not convert malformed or unsupported readiness into success',async data => {
  vi.stubGlobal('fetch',vi.fn(async () => new Response(JSON.stringify(data)))); render(<ResearchSetup />);
  expect(await screen.findByText(/Research settings unavailable/)).toBeTruthy();
  expect(screen.queryByText('quick-fixture')).toBeNull();
});
