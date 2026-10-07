import { act, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import Analysis from './Analysis';

afterEach(() => { vi.unstubAllGlobals(); window.history.replaceState(null, '', '#/analysis'); });

it('reloads a verified continuation report without rewriting the failed original run', async () => {
  const runId = '11111111-1111-4111-8111-111111111111';
  const reportId = '22222222-2222-4222-8222-222222222222';
  const decisionId = '33333333-3333-4333-8333-333333333333';
  const run = {run_id:runId,instrument_id:'apple',status:'failed',created_at:'2026-10-07T00:00:00Z',
    analysis_as_of:'2026-10-07T00:00:00Z',selected_analysts:['market'],snapshot_ids:['saved-source']};
  let published = false;
  let artifactReads = 0;
  vi.stubGlobal('EventSource',vi.fn(function(){return {addEventListener:vi.fn(),close:vi.fn()};}));
  vi.stubGlobal('fetch',vi.fn(async(url:string) => {
    let value: unknown = run;
    if (url.includes('/instruments?')) value = [];
    else if (url.includes('/runs?')) value = [run];
    else if (url.includes('/continuations?')) {
      published = true;
      value = {items:[{run_id:runId,execution_id:'44444444-4444-4444-8444-444444444444',attempt:2,status:'completed',
        preparation_requires_review:false,lease_expired:true,report_artifact_id:reportId,evidence_artifact_id:null,decision_id:decisionId}],has_more:false};
    } else if (url.endsWith('/events')) value = {events:[],has_more:false,approval_eligible:false};
    else if (url.includes('/artifacts?')) {
      artifactReads++;
      value = published ? [{artifact_id:reportId,kind:'analysis_report',media_type:'application/json',
        byte_size:500,content_hash:'sha256:fixture',created_at:run.created_at}] : [];
    } else if (url.endsWith(`/artifacts/${reportId}`)) value = {run_id:runId,decision_id:decisionId,
      profile:'equity',reference_only:false,selected_analysts:['market'],snapshot_attestation:'PASS',
      narrative:'Verified continuation fixture',structured_narrative:null,validation_issues:['structured_output_missing']};
    return new Response(JSON.stringify(value));
  }));
  // Flush the initial history/detail/continuation promise chain inside React's
  // async boundary before asserting the rendered result. Do not extend the
  // assertion deadline or substitute a successful original-run status.
  await act(async () => { render(<Analysis />); });
  await screen.findByRole('heading',{name:'Continuation report available'});
  await screen.findByText('Verified continuation fixture');
  expect(artifactReads).toBeGreaterThan(1);
  expect(within(screen.getByRole('region',{name:'Analysis history'})).getByText('Research failed')).toBeTruthy();
  expect(screen.getByText(/The model response did not pass/)).toBeTruthy();
});

it('separates failed-run working notes from completed reports and fetches only on reader request', async () => {
  const date = '2026-09-26T00:00:00Z';
  const run = {run_id:'failed-run',instrument_id:'apple',status:'failed',created_at:date,
    analysis_as_of:date,selected_analysts:['market'],snapshot_ids:[]};
  const artifact = {artifact_id:'stage-note',kind:'research_stage',media_type:'application/json',
    byte_size:500,content_hash:'synthetic',created_at:date};
  const note = {schema_version:'1.0',run_id:run.run_id,stage:'Market Analyst',attempt:1,
    sequence:1,analysis_as_of:date,research_quality:'unvalidated',approval_eligible:false,
    sections:{market_report:'Synthetic saved working note'}};
  vi.stubGlobal('EventSource',vi.fn(function(){return {addEventListener:vi.fn(),close:vi.fn()};}));
  const fetch = vi.fn(async(url:string)=>new Response(JSON.stringify(url.includes('/instruments?') ? []
    : url.includes('/artifacts?') ? [artifact] : url.endsWith('/artifacts/stage-note') ? note
      : url.includes('/runs?') ? [run] : run)));
  vi.stubGlobal('fetch',fetch); render(<Analysis />);
  expect(await screen.findByText('No completed report was published for this run.')).toBeTruthy();
  expect(screen.getByText('Research allowance was not recorded for this run.')).toBeTruthy();
  const summary = screen.getByText(/Saved working notes/);
  expect(summary.closest('details')?.open).toBe(false);
  expect(fetch.mock.calls.some(([url])=>url.endsWith('/artifacts/stage-note'))).toBe(false);
  const user=userEvent.setup();await user.click(summary);
  await user.click(screen.getByRole('button',{name:'Inspect research stage'}));
  expect(await screen.findByText('Synthetic saved working note')).toBeTruthy();
  expect(screen.queryByRole('link',{name:'Review linked decision'})).toBeNull();
});

it('leads completed research with its report and preserves processing in a collapsed disclosure', async () => {
  const run = {run_id:'saved-run',instrument_id:'apple',status:'succeeded',created_at:'2026-09-26T00:00:00Z',
    analysis_as_of:'2026-09-26T00:00:00Z',selected_analysts:['market'],snapshot_ids:['source'],
    execution_limits:{wall_seconds:3600,model_calls:128}};
  const artifacts = ['decision_evidence','analysis_report'].map(kind => ({artifact_id:kind,kind,
    media_type:'application/json',byte_size:500,content_hash:'sha256:fixture',created_at:run.created_at}));
  const report = {run_id:run.run_id,decision_id:'12345678-1234-1234-1234-123456789abc',profile:'equity',
    reference_only:false,selected_analysts:['market'],snapshot_attestation:'PASS',
    narrative:'Saved research content',structured_narrative:null,validation_issues:['structured_output_missing']};
  vi.stubGlobal('EventSource',vi.fn(function(){return {addEventListener:vi.fn(),close:vi.fn()};}));
  const fetch = vi.fn(async(url:string) => new Response(JSON.stringify(
    url.includes('/instruments?') ? [] : url.includes('/artifacts?') ? artifacts :
      url.endsWith('/artifacts/analysis_report') ? report : url.includes('/runs?') ? [run] : run)));
  vi.stubGlobal('fetch',fetch);
  const user = userEvent.setup(); render(<Analysis />);
  await screen.findByRole('heading',{name:'Research brief'});
  const processing = screen.getByText('Completed analysis · View processing details').closest('details')!;
  expect(processing.open).toBe(false);
  expect(screen.getByText(/The model response did not pass/)).toBeTruthy();
  expect(document.querySelector('.artifact-list > li .artifact-preview')).not.toBeNull();
  const calls = fetch.mock.calls.length;
  await user.click(screen.getByText('Completed analysis · View processing details'));
  expect(processing.open).toBe(true);
  expect(within(processing).getByRole('heading',{name:'Research progress'})).toBeTruthy();
  expect(within(processing).getByText('Recorded research allowance: 60 minutes')).toBeTruthy();
  expect(fetch.mock.calls.length).toBe(calls);
});

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
  act(() => {
    window.history.replaceState(null, '', '#/analysis?run=another-run');
    window.dispatchEvent(new HashChangeEvent('hashchange'));
  });
  await waitFor(() => expect(fetch.mock.calls.some(([url]) => url.endsWith('/runs/another-run'))).toBe(true));
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
