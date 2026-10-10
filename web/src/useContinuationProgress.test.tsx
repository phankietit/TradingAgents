import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { useContinuationProgress } from './useContinuationProgress';

afterEach(() => vi.unstubAllGlobals());
const event = (sequence:number) => ({sequence,event_type:'stage.started',occurred_at:'2026-10-07T00:00:00Z',attempt:2,stage:'Market Analyst'});
const page = (sequence:number) => new Response(JSON.stringify({events:[event(sequence)],has_more:false,approval_eligible:false}));

it('coalesces polling without aborting an in-flight page and hides prior execution progress on selection change', async () => {
  let release!: (value:Response)=>void;
  let firstSignal!:AbortSignal;
  const fetch = vi.fn(async(url:string,init?:RequestInit)=>{
    if (url==='/api/v1/first/events' && !release) {
      firstSignal=init!.signal as AbortSignal;
      return new Promise<Response>(resolve=>{release=resolve;});
    }
    return url.includes('after_sequence=1')
      ? new Response(JSON.stringify({events:[],has_more:false,approval_eligible:false})) : page(9);
  });
  vi.stubGlobal('fetch',fetch);
  const {result,rerender}=renderHook(({path,version})=>useContinuationProgress(path,2,version),
    {initialProps:{path:'/first/events',version:0}});
  await waitFor(()=>expect(release).toBeTypeOf('function'));
  rerender({path:'/first/events',version:1});
  expect(firstSignal.aborted).toBe(false);
  expect(fetch).toHaveBeenCalledTimes(1);
  await act(async()=>release(page(1)));
  await waitFor(()=>expect(result.current.loading).toBe(false));
  expect(result.current.data?.events.map(item=>item.sequence)).toEqual([1]);
  expect(fetch.mock.calls.map(call=>call[0])).toEqual(['/api/v1/first/events','/api/v1/first/events?after_sequence=1']);
  rerender({path:'/second/events',version:1});
  expect(result.current.data).toBeUndefined();
  expect(firstSignal.aborted).toBe(true);
  await waitFor(()=>expect(result.current.data?.events[0].sequence).toBe(9));
});

it('clears the display and cursor after invalid later progress and revalidates from the beginning on retry', async () => {
  let broken=false;
  const fetch=vi.fn(async(url:string)=>broken ? new Response('',{status:409}) : url.includes('after_sequence')
    ? new Response(JSON.stringify({events:[],has_more:false,approval_eligible:false})) : page(1));
  vi.stubGlobal('fetch',fetch);
  const {result,rerender}=renderHook(({version})=>useContinuationProgress('/first/events',2,version),{initialProps:{version:0}});
  await waitFor(()=>expect(result.current.data?.events[0].sequence).toBe(1));
  broken=true;rerender({version:1});
  await waitFor(()=>expect(result.current.error).toBeDefined());
  expect(result.current.data).toBeUndefined();
  broken=false;rerender({version:2});
  await waitFor(()=>expect(result.current.data?.events[0].sequence).toBe(1));
  expect(fetch.mock.calls.at(-1)?.[0]).toBe('/api/v1/first/events');
});
