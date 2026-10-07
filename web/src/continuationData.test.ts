import { expect, it } from 'vitest';
import { continuation, discovery, preparation, progress } from './continuationData';
const runId = '11111111-1111-4111-8111-111111111111';
const item = {run_id:runId,execution_id:'22222222-2222-4222-8222-222222222222',attempt:2,status:'reserved',
  preparation_requires_review:false,lease_expired:false,report_artifact_id:null,evidence_artifact_id:null,decision_id:null};
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
});
