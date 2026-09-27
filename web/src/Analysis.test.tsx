import { act, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import Analysis from './Analysis';

afterEach(() => vi.unstubAllGlobals());

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
    .getByText('Research complete')).toBeTruthy());
  expect(screen.queryByRole('button', { name: 'Cancel run' })).toBeNull();
  expect(stream).toHaveBeenCalledTimes(1);
  expect(close).toHaveBeenCalled();
});
