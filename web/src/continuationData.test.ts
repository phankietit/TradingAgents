import { afterEach, expect, it, vi } from 'vitest';
import { continuation, discovery, preparation, progress, readProgress } from './continuationData';
afterEach(() => vi.unstubAllGlobals());
const runId = '11111111-1111-4111-8111-111111111111';
const item = {run_id:runId,execution_id:'22222222-2222-4222-8222-222222222222',attempt:2,status:'reserved',
  preparation_requires_review:false,lease_expired:false,report_artifact_id:null,evidence_artifact_id:null,decision_id:null};
it('admits local stop only behind a publication fence without cost or retry authority', () => {
  const local_stop = {stopped_at:'2026-10-07T00:00:00Z',continuation_authorized:false as const,provider_cost_known:false as const};
  expect(continuation({...item,status:'cancel_requested',local_stop},runId).local_stop).toBe(local_stop);
  expect(continuation({...item,status:'leased',lease_expired:true,local_stop},runId).local_stop).toBe(local_stop);
  for (const status of ['reserved','leased','cancelled','completed']) {
    expect(() => continuation({...item,status,local_stop},runId)).toThrow();
  }
  for (const change of [{provider_cost_known:true},{continuation_authorized:true},{stopped_at:'invalid'},
    {stopped_at:'2026-10-07T00:00:00'},{extra:true}]) {
    expect(() => continuation({...item,status:'cancel_requested',local_stop:{...local_stop,...change} as typeof local_stop},runId)).toThrow();
  }
});
it('does not promote reservation IDs, wrong ownership or corrupt completion into report authority', () => {
  expect(continuation(item,runId)).toBe(item);
  expect(() => continuation({...item,run_id:'different'},runId)).toThrow();
  expect(() => continuation({...item,status:'completed'},runId)).toThrow();
  expect(() => continuation({...item,report_artifact_id:item.execution_id},runId)).toThrow();
  const completed = {...item,status:'completed',lease_expired:true,report_artifact_id:item.execution_id,decision_id:item.execution_id};
  expect(continuation(completed,runId).status).toBe('completed');
});
it('rejects duplicate discovery and false or changed disclosure contracts', () => {
  expect(() => discovery({items:[item,item],has_more:false},runId)).toThrow();
  expect(() => discovery({items:[],has_more:true},runId)).toThrow();
  const prepared = {run_id:runId,observation_hash:'a'.repeat(64),remaining_wall_seconds:600,
    remaining_model_calls:8,dispatch_enabled:false as const,
    disclosures:['original_allowance_retained','provider_cost_unknown','prior_research_unvalidated']};
  expect(preparation(prepared,runId)).toBe(prepared);
  expect(() => preparation({...prepared,remaining_wall_seconds:Infinity},runId)).toThrow();
  expect(() => preparation({...prepared,disclosures:[]},runId)).toThrow();
});
it('rejects original-attempt or unordered event replay and approval-bearing progress', () => {
  const event = {sequence:5,event_type:'stage.started',occurred_at:'2026-10-07T00:00:00Z',attempt:2,stage:'Market Analyst'};
  expect(progress({events:[event],has_more:false,approval_eligible:false},2).events).toHaveLength(1);
  expect(() => progress({events:[{...event,attempt:1}],has_more:false,approval_eligible:false},2)).toThrow();
  expect(() => progress({events:[event,event],has_more:false,approval_eligible:false},2)).toThrow();
  expect(() => progress({events:[],has_more:true,approval_eligible:false},2)).toThrow();
});

const event = (sequence:number) => ({sequence,event_type:'stage.started',occurred_at:'2026-10-07T00:00:00Z',attempt:2,stage:'Market Analyst'});
it('consumes all pages beyond the first hundred events and polls only after the validated cursor', async () => {
  const pages = [
    {events:Array.from({length:100},(_,index)=>event(index+1)),has_more:true,approval_eligible:false},
    {events:[event(101)],has_more:false,approval_eligible:false},
    {events:[event(102)],has_more:false,approval_eligible:false},
  ];
  const fetch = vi.fn(async(url:string)=>{
    expect(url.startsWith('/api/v1/progress/events')).toBe(true);
    return new Response(JSON.stringify(pages.shift()));
  });
  vi.stubGlobal('fetch',fetch);
  const signal = new AbortController().signal;
  const first = await readProgress('/progress/events',2,signal);
  expect(first.events.map(item=>item.sequence)).toEqual(Array.from({length:101},(_,index)=>index+1));
  expect(first.has_more).toBe(false);
  expect(fetch.mock.calls.map(call=>String(call[0]))).toEqual(['/api/v1/progress/events','/api/v1/progress/events?after_sequence=100']);
  const next = await readProgress('/progress/events',2,signal,first.events);
  expect(next.events.at(-1)?.sequence).toBe(102);
  expect(first.events).toHaveLength(101);
  expect(fetch.mock.calls.at(-1)?.[0]).toBe('/api/v1/progress/events?after_sequence=101');
});

it('refuses a repeated cross-page cursor or failed later page instead of publishing partial progress', async () => {
  for (const next of [{events:[event(1)],has_more:false,approval_eligible:false},null]) {
    let reads=0;
    vi.stubGlobal('fetch',vi.fn(async()=>{
      reads++;
      return reads===1 ? new Response(JSON.stringify({events:[event(1)],has_more:true,approval_eligible:false}))
        : next ? new Response(JSON.stringify(next)) : new Response('',{status:409});
    }));
    await expect(readProgress('/progress/events',2,new AbortController().signal)).rejects.toThrow();
    expect(reads).toBe(2);
  }
});

it('aborts before paging or publishing when the selected execution changes', async () => {
  const controller = new AbortController();
  const fetch = vi.fn(async()=>{
    controller.abort();
    return new Response(JSON.stringify({events:[event(1)],has_more:true,approval_eligible:false}));
  });
  vi.stubGlobal('fetch',fetch);
  await expect(readProgress('/progress/events',2,controller.signal)).rejects.toThrow();
  expect(fetch).toHaveBeenCalledTimes(1);
  await expect(readProgress('/progress/events',2,controller.signal)).rejects.toThrow();
  expect(fetch).toHaveBeenCalledTimes(1);
});
