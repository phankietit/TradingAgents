import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import ContinuationPanel from './ContinuationPanel';

afterEach(() => vi.unstubAllGlobals());
const runId = '11111111-1111-4111-8111-111111111111';
const executionId = '22222222-2222-4222-8222-222222222222';
const saved = {run_id:runId,execution_id:executionId,attempt:2,status:'reserved',
  preparation_requires_review:false,lease_expired:false,report_artifact_id:null,evidence_artifact_id:null,decision_id:null};

it('never prepares or reserves automatically and requires all disclosures before explicit consent', async () => {
  let reserved = false;
  const writes: {path:string; body:Record<string,unknown>|undefined}[] = [];
  vi.stubGlobal('fetch',vi.fn(async (url:string, init?:RequestInit) => {
    if (init?.method === 'POST') writes.push({path:url,body:init.body ? JSON.parse(String(init.body)) : undefined});
    const value = url.endsWith('/auth/csrf') ? {csrf_token:'synthetic-csrf'} : url.endsWith('/continuation/prepare')
      ? {run_id:runId,observation_hash:'a'.repeat(64),remaining_wall_seconds:600,remaining_model_calls:8,dispatch_enabled:false,
        disclosures:['original_allowance_retained','provider_cost_unknown','prior_research_unvalidated']}
      : init?.method === 'POST' && url.endsWith('/continuations') ? (reserved = true, {run_id:runId,execution_id:executionId,status:'reserved',dispatch_enabled:false})
        : url.endsWith('/events') ? {events:[],has_more:false,approval_eligible:false}
          : {items:reserved ? [saved] : [],has_more:false};
    return new Response(JSON.stringify(value));
  }));
  render(<ContinuationPanel runId={runId} version={0} onReports={vi.fn()} onNewAttempt={vi.fn()} />);
  const prepare = await screen.findByRole('button',{name:'Check saved continuation'});
  expect(writes).toHaveLength(0);
  const user = userEvent.setup(); await user.click(prepare);
  const confirm = await screen.findByRole('button',{name:'Confirm and continue'});
  expect(confirm.hasAttribute('disabled')).toBe(true);
  const checks = screen.getAllByRole('checkbox');
  await user.click(checks[0]); await user.click(checks[1]);
  expect(confirm.hasAttribute('disabled')).toBe(true);
  expect(writes.filter(write => write.path.endsWith('/continuations'))).toHaveLength(0);
  await user.click(checks[2]); await user.click(confirm);
  await screen.findByText(/Processing starts only when the local continuation service is enabled/);
  const reservations = writes.filter(write => write.path.endsWith('/continuations'));
  expect(reservations).toHaveLength(1);
  expect(reservations[0].body).toMatchObject({confirm_continue:true,acknowledge_original_allowance:true,
    acknowledge_unknown_provider_cost:true,acknowledge_unvalidated_prior_research:true});
  expect(screen.queryByRole('button',{name:'Check saved continuation'})).toBeNull();
});

it('shows verified completion despite an old lease and does not expose a retry/stop authority', async () => {
  const completed = {...saved,status:'completed',lease_expired:true,report_artifact_id:executionId,decision_id:executionId};
  vi.stubGlobal('fetch',vi.fn(async(url:string) => new Response(JSON.stringify(url.endsWith('/events')
    ? {events:[],has_more:false,approval_eligible:false} : {items:[completed],has_more:false}))));
  const onReports = vi.fn();
  render(<ContinuationPanel runId={runId} version={0} onReports={onReports} onNewAttempt={vi.fn()} />);
  await screen.findByRole('heading',{name:'Continuation report available'});
  await waitFor(() => expect(onReports).toHaveBeenCalledWith([executionId]));
  expect(screen.queryByRole('button',{name:'Stop continuation'})).toBeNull();
  expect(screen.queryByText(/Processing could not continue safely/)).toBeNull();
  expect(screen.getByText(/Completion does not mean/)).toBeTruthy();
});
