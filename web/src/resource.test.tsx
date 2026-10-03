import {act, renderHook, waitFor} from '@testing-library/react';
import {afterEach, expect, it, vi} from 'vitest';
import {useResource} from './data';

afterEach(() => vi.unstubAllGlobals());
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
