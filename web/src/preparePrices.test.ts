import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { ApiError, mutate } from './api';
import { preparePrices } from './preparePrices';
vi.mock('./api', async original => ({ ...await original<typeof import('./api')>(), mutate: vi.fn() }));
const response = (status: string, extra = {}) => ({ status, snapshot: null, analysis_as_of: '', reused: false, ...extra });
beforeEach(() => { vi.useFakeTimers(); vi.mocked(mutate).mockReset(); });
afterEach(() => { vi.clearAllTimers(); vi.useRealTimers(); });

it('waits 60 then 120 seconds and succeeds on the third check', async () => {
  vi.mocked(mutate).mockResolvedValueOnce(response('stale')).mockResolvedValueOnce(response('coverage_gap')).mockResolvedValueOnce(response('ready'));
  const progress = vi.fn();
  const pending = preparePrices('BTC', new AbortController().signal, progress);
  await vi.advanceTimersByTimeAsync(0);
  expect(progress).toHaveBeenLastCalledWith({ attempt: 1, remaining: 60, waiting: true, reason: 'stale' });
  await vi.advanceTimersByTimeAsync(59_000);
  expect(mutate).toHaveBeenCalledTimes(1);
  await vi.advanceTimersByTimeAsync(1000);
  expect(mutate).toHaveBeenCalledTimes(2);
  await vi.advanceTimersByTimeAsync(120_000);
  expect(await pending).toMatchObject({status:'ready',checks:3});
  expect(mutate).toHaveBeenCalledTimes(3);
});

it('stops after three checks and retains the cause across local cooldown', async () => {
  vi.mocked(mutate).mockResolvedValueOnce(response('stale')).mockResolvedValue(response('cooldown', {retry_after_seconds:60,last_failure:'stale'}));
  const pending = preparePrices('BTC', new AbortController().signal, vi.fn());
  await vi.advanceTimersByTimeAsync(180_000);
  expect(await pending).toMatchObject({status:'cooldown',last_failure:'stale',checks:3});
  await vi.advanceTimersByTimeAsync(600_000);
  expect(mutate).toHaveBeenCalledTimes(3);
});

it('cancels waiting without another request', async () => {
  vi.mocked(mutate).mockResolvedValue(response('coverage_gap'));
  const controller = new AbortController();
  const pending = preparePrices('BTC', controller.signal, vi.fn());
  const rejected = expect(pending).rejects.toMatchObject({ name:'AbortError' });
  await vi.advanceTimersByTimeAsync(0);
  controller.abort();
  await rejected;
  await vi.advanceTimersByTimeAsync(600_000);
  expect(mutate).toHaveBeenCalledTimes(1);
});

it('respects a longer server retry hint', async () => {
  vi.mocked(mutate).mockResolvedValueOnce(response('rate_limited',{retry_after_seconds:120})).mockResolvedValue(response('ready'));
  const pending=preparePrices('BTC',new AbortController().signal,vi.fn());
  await vi.advanceTimersByTimeAsync(119_000);
  expect(mutate).toHaveBeenCalledTimes(1);
  await vi.advanceTimersByTimeAsync(1000);
  expect(await pending).toMatchObject({status:'ready'});
});

it('does not retry authentication or permanent validation failures', async () => {
  vi.mocked(mutate).mockRejectedValueOnce(new ApiError(401));
  await expect(preparePrices('BTC',new AbortController().signal,vi.fn())).rejects.toMatchObject({status:401});
  expect(mutate).toHaveBeenCalledTimes(1);
  vi.mocked(mutate).mockResolvedValueOnce(response('invalid'));
  expect(await preparePrices('BTC',new AbortController().signal,vi.fn())).toMatchObject({status:'invalid',checks:1});
});

it('retries a transient network failure but never submits an AI run', async () => {
  vi.mocked(mutate).mockRejectedValueOnce(new ApiError(0)).mockResolvedValueOnce(response('ready'));
  const pending=preparePrices('BTC',new AbortController().signal,vi.fn());
  await vi.advanceTimersByTimeAsync(60_000);
  expect(await pending).toMatchObject({status:'ready',checks:2});
  expect(vi.mocked(mutate).mock.calls.every(([path]) => path.endsWith('/prepare-data'))).toBe(true);
});
