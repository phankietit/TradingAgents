import {act, renderHook, waitFor} from '@testing-library/react';
import {afterEach, expect, it, vi} from 'vitest';
import {useResource} from './data';

afterEach(() => vi.unstubAllGlobals());
it('coalesces repeated polling ticks instead of starving a slow status request', async () => {
  let release!: (value:Response) => void;
  let signal!: AbortSignal;
  const fetch = vi.fn().mockImplementationOnce((_url:string, init:RequestInit) => {
    signal = init.signal as AbortSignal;
    return new Promise<Response>(resolve => {release = resolve;});
  }).mockResolvedValue(new Response(JSON.stringify({status:'succeeded'})));
  vi.stubGlobal('fetch', fetch);
  const view = renderHook(({version}) => useResource<{status:string}>('/runs/slow',version,undefined,true),
    {initialProps:{version:0}});
  await waitFor(() => expect(release).toBeTypeOf('function'));
  view.rerender({version:1});
  view.rerender({version:2});
  expect(signal.aborted).toBe(false);
  expect(fetch).toHaveBeenCalledTimes(1);
  await act(async () => release(new Response(JSON.stringify({status:'running'}))));
  await waitFor(() => expect(view.result.current.data?.status).toBe('succeeded'));
  expect(fetch).toHaveBeenCalledTimes(2);
});
it('keeps read-only polling content while refreshing and clears it on failure', async () => {
  let resolve!: (value: Response) => void;
  const fetch = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({status:'running'})))
    .mockImplementationOnce(() => new Promise<Response>(done => {resolve = done;}));
  vi.stubGlobal('fetch', fetch);
  const view = renderHook(({version}) => useResource<{status:string}>('/runs/one',version,undefined,true),{initialProps:{version:0}});
  await waitFor(() => expect(view.result.current.data?.status).toBe('running'));
  view.rerender({version:1});
  expect(view.result.current.loading).toBe(false);
  expect(view.result.current.data?.status).toBe('running');
  await act(async () => resolve(new Response('{}',{status:503})));
  await waitFor(() => expect(view.result.current.error).toBeTruthy());
  expect(view.result.current.data).toBeUndefined();
});
it('aborts old identity and ignores its late response and queued refresh', async () => {
  let release!: (value:Response) => void;
  let signal!: AbortSignal;
  const fetch = vi.fn().mockImplementationOnce((_url:string, init:RequestInit) => {
    signal = init.signal as AbortSignal;
    return new Promise<Response>(resolve => {release=resolve;});
  }).mockResolvedValue(new Response(JSON.stringify({status:'second-run'})));
  vi.stubGlobal('fetch',fetch);
  const view=renderHook(({path,version})=>useResource<{status:string}>(path,version,undefined,true),
    {initialProps:{path:'/runs/first',version:0}});
  await waitFor(()=>expect(release).toBeTypeOf('function'));
  view.rerender({path:'/runs/first',version:1});
  view.rerender({path:'/runs/second',version:1});
  expect(signal.aborted).toBe(true);
  await waitFor(()=>expect(view.result.current.data?.status).toBe('second-run'));
  await act(async()=>release(new Response(JSON.stringify({status:'old-run'}))));
  expect(view.result.current.data?.status).toBe('second-run');
  expect(fetch.mock.calls.map(call=>call[0])).toEqual(['/api/v1/runs/first','/api/v1/runs/second']);
});
it('does not start a queued refresh after leaving the polling surface', async () => {
  let release!: (value:Response) => void;
  let signal!: AbortSignal;
  const fetch=vi.fn((_url:string, init:RequestInit)=>{
    signal=init.signal as AbortSignal;
    return new Promise<Response>(resolve=>{release=resolve;});
  });
  vi.stubGlobal('fetch',fetch);
  const view=renderHook(({version})=>useResource('/runs/first',version,undefined,true),{initialProps:{version:0}});
  await waitFor(()=>expect(release).toBeTypeOf('function'));
  view.rerender({version:1});
  view.unmount();
  expect(signal.aborted).toBe(true);
  await act(async()=>release(new Response(JSON.stringify({status:'late'}))));
  expect(fetch).toHaveBeenCalledTimes(1);
});
it('never carries polling content across resource identities', async () => {
  vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({status:'running'})))
    .mockImplementationOnce(() => new Promise(() => {})));
  const view = renderHook(({path}) => useResource<{status:string}>(path,0,undefined,true),{initialProps:{path:'/runs/one'}});
  await waitFor(() => expect(view.result.current.data).toBeTruthy());
  view.rerender({path:'/runs/two'});
  expect(view.result.current.data).toBeUndefined();
  expect(view.result.current.loading).toBe(true);
});
it('keeps the fail-closed default for decision and approval refreshes', async () => {
  vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({status:'ready_for_approval'})))
    .mockImplementationOnce(() => new Promise(() => {})));
  const view = renderHook(({version}) => useResource('/decisions/one',version),{initialProps:{version:0}});
  await waitFor(() => expect(view.result.current.data).toBeTruthy());
  view.rerender({version:1});
  expect(view.result.current.data).toBeUndefined();
  expect(view.result.current.loading).toBe(true);
});
