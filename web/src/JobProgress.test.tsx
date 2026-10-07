import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import JobProgress from './JobProgress';

afterEach(()=>vi.unstubAllGlobals());
const job = {job_id:'job-fixture',run_id:'run-fixture',status:'retry_wait',attempt:1,max_attempts:3,available_at:'2026-09-27T01:00:00Z',updated_at:'2026-09-27T00:00:00Z',completed_at:null};
it('renders saved attempts and retry timing without implying an ETA or active worker',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify(job))));
  render(<JobProgress runId="run-fixture" version={0} />);
  expect(await screen.findByText('Waiting to retry')).toBeTruthy();
  expect(screen.getByText(/Attempt 1 of 3/)).toBeTruthy();
  expect(screen.getByText(/no earlier than/)).toBeTruthy();
  expect(screen.getByText(/further model charges/)).toBeTruthy();
  expect(screen.getByText('job-fixture').closest('details')?.open).toBe(false);
});
it.each([{}, {...job,run_id:'other'}, {...job,attempt:4}])('withholds invalid or mismatched processing state',async value=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify(value))));
  render(<JobProgress runId="run-fixture" version={0} />);
  expect(await screen.findByText(/Processing details unavailable/)).toBeTruthy();
  expect(screen.queryByText('Waiting to retry')).toBeNull();
});
it('shows absent processing record without inventing a running job',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response('{}',{status:404})));
  render(<JobProgress runId="run-fixture" version={0} />);
  expect(await screen.findByText(/No processing record was found/)).toBeTruthy();
});

it.each([404, 503])('withdraws the previous observed status after a %s refresh failure', async status => {
  const onStatus = vi.fn();
  vi.stubGlobal('fetch', vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify({...job, status:'succeeded'})))
    .mockResolvedValueOnce(new Response('{}', {status})));
  const view = render(<JobProgress runId="run-fixture" version={0} onStatus={onStatus} />);
  await screen.findByText('Processing complete');
  await waitFor(() => expect(onStatus).toHaveBeenLastCalledWith('succeeded'));
  view.rerender(<JobProgress runId="run-fixture" version={1} onStatus={onStatus} />);
  await screen.findByText(/Processing details unavailable/);
  expect(screen.queryByText('Processing complete')).toBeNull();
  await waitFor(() => expect(onStatus).toHaveBeenLastCalledWith(null));
});

it('withdraws a previous observation when the refreshed job belongs to another run', async () => {
  const onStatus = vi.fn();
  vi.stubGlobal('fetch', vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify(job)))
    .mockResolvedValueOnce(new Response(JSON.stringify({...job, run_id:'other'}))));
  const view = render(<JobProgress runId="run-fixture" version={0} onStatus={onStatus} />);
  await screen.findByText('Waiting to retry');
  await waitFor(() => expect(onStatus).toHaveBeenLastCalledWith('retry_wait'));
  view.rerender(<JobProgress runId="run-fixture" version={1} onStatus={onStatus} />);
  await screen.findByText(/Processing details unavailable/);
  await waitFor(() => expect(onStatus).toHaveBeenLastCalledWith(null));
});
