import { act, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import Analysis from './Analysis';

afterEach(() => { vi.unstubAllGlobals(); window.history.replaceState(null, '', '#/analysis'); });

it('opens the exact deep-linked run outside the history page instead of another run', async () => {
  window.history.replaceState(null, '', '#/analysis?run=older-run');
  vi.stubGlobal('EventSource', vi.fn(function () { return {addEventListener:vi.fn(),close:vi.fn()}; }));
  const latest = {run_id:'latest',instrument_id:'apple',status:'succeeded',created_at:'2026-09-26T00:00:00Z'};
  const fetch = vi.fn(async (url:string) => new Response(JSON.stringify(
    url.includes('/instruments?') || url.includes('/artifacts?') ? [] : url.includes('/runs?') ? [latest] :
      {...latest,run_id:'older-run',analysis_as_of:'2026-09-20T00:00:00Z',selected_analysts:['market'],snapshot_ids:[]}
  )));
  vi.stubGlobal('fetch', fetch);
  render(<Analysis />);
  await screen.findByText(/2026-09-20 00:00:00 UTC/);
  expect(fetch.mock.calls.some(([url]) => url.endsWith('/runs/older-run'))).toBe(true);
  expect(fetch.mock.calls.some(([url]) => url.endsWith('/runs/latest'))).toBe(false);
});

it('explains failed research and keeps its diagnostic code collapsed', async () => {
  const run = {run_id:'failed-run',instrument_id:'apple',status:'failed',created_at:'2026-09-26T00:00:00Z',analysis_as_of:'2026-09-26T00:00:00Z',selected_analysts:['market'],snapshot_ids:[],error_code:'HANDLER_ERROR'};
  vi.stubGlobal('EventSource',vi.fn(function(){return {addEventListener:vi.fn(),close:vi.fn()};}));
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>new Response(JSON.stringify(url.includes('/instruments?') || url.includes('/artifacts?') ? [] : url.includes('/runs?') ? [run] : run))));
  render(<Analysis />);
  expect(await screen.findByText(/Research could not be completed. No investment conclusion/)).toBeTruthy();
  expect(screen.getByText('HANDLER_ERROR').closest('details')?.open).toBe(false);
  expect(screen.getByRole('button',{name:'Configure new attempt'})).toBeTruthy();
  expect(screen.queryByRole('button',{name:'Cancel run'})).toBeNull();
});

it('updates the history row from refreshed detail without reconnecting the event stream', async () => {
  let status = 'queued';
  const listeners = new Map<string, (event: MessageEvent) => void>();
  const close = vi.fn();
  const stream = vi.fn(function () {
    return { addEventListener: (name: string, listener: (event: MessageEvent) => void) => listeners.set(name, listener), close };
  });
  vi.stubGlobal('EventSource', stream);
  const run = { run_id: 'fixture-run', instrument_id: 'fixture-apple', status: 'queued',
    created_at: '2026-09-26T00:00:00Z', analysis_as_of: '2026-09-26T00:00:00Z',
    selected_analysts: ['market'], snapshot_ids: ['fixture-source'] };
  vi.stubGlobal('fetch', vi.fn(async (url: string) => new Response(JSON.stringify(
    url.includes('/instruments?') ? [] : url.includes('/runs?') ? [run] :
      url.includes('/artifacts?') ? [] : { ...run, status },
  ))));
  render(<Analysis />);
  expect(await within(screen.getByRole('region', { name: 'Analysis history' })).findByText('Waiting to start')).toBeTruthy();
  await screen.findByRole('button', { name: 'Cancel run' });
  status = 'succeeded';
  act(() => listeners.get('run.succeeded')!(new MessageEvent('run.succeeded', {
    data: JSON.stringify({ sequence: 1, event_type: 'run.succeeded', occurred_at: run.created_at }),
  })));
  await waitFor(() => expect(within(screen.getByRole('region', { name: 'Analysis history' }))
    .getByText('Processing complete')).toBeTruthy());
  expect(screen.queryByRole('button', { name: 'Cancel run' })).toBeNull();
  expect(stream).toHaveBeenCalledTimes(1);
  expect(close).toHaveBeenCalled();
});
