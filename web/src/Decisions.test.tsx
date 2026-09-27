import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import Decisions from './Decisions';
import type { Decision } from './Decisions';
const candidate: Decision = { decision_id: 'decision-fixture', run_id: 'run-fixture', instrument_id: 'aapl', as_of: '2026-09-01T00:00:00Z', status: 'review', rating: 'Review', confidence: .5, thesis: '<script>not executable</script>', risks: ['Synthetic risk'], invalidation_conditions: ['Synthetic invalidation'], data_quality: 'STALE', current_weight: null, target_weight: null, max_allowed_weight: null, portfolio_snapshot_id: null, policy_checks: [], evidence: [] };
beforeEach(() => {
  window.history.replaceState(null, '', '#/decisions');
  HTMLDialogElement.prototype.showModal = function() { this.setAttribute('open', ''); };
  HTMLDialogElement.prototype.close = function() { this.removeAttribute('open'); };
});
afterEach(() => { vi.unstubAllGlobals(); window.history.replaceState(null, '', '#/decisions'); });
function setup(rejectFails = false, selectedCandidate = candidate) {
  let rejected = false;
  const fetch = vi.fn(async (url: string, init: RequestInit) => {
    const state = { candidate: selectedCandidate, current_status: rejected ? 'rejected' : 'review', events: rejected ? [{ event_id: 'event', from_status: 'review', to_status: 'rejected', actor_type: 'owner', occurred_at: candidate.as_of, reason: 'Insufficient evidence' }] : [] };
    if (url.endsWith('/transitions')) { if (rejectFails) return new Response('{}', {status:409}); expect(init.method).toBe('POST'); rejected = true; return new Response(JSON.stringify(state)); }
    if (url.endsWith('/auth/csrf')) return new Response(JSON.stringify({ csrf_token: 'fixture' }));
    if (url.endsWith('/state')) return new Response(JSON.stringify(state));
    if (url.includes('/runs/')) return new Response(JSON.stringify({ status: 'succeeded' }));
    return new Response(JSON.stringify(url.includes('/decisions?') ? [candidate] : []));
  });
  vi.stubGlobal('fetch', fetch); return fetch;
}
it('renders narrative as text and disables approval for REVIEW', async () => {
  setup(); render(<Decisions />);
  expect(await screen.findByText(candidate.thesis)).toBeTruthy();
  expect(document.querySelector('script')).toBeNull();
  expect((screen.getByRole('button', {name:'Approve decision'}) as HTMLButtonElement).disabled).toBe(true);
});
it('presents financial risk percentages without changing review eligibility',async()=>{
  const value={...candidate,policy_checks:[{check_id:'max_position_weight',policy_id:'p',policy_version:'1',result:'PASS',blocking:true,reason:'Within allocation limit',observed_value:0.2,limit_value:0.3}]};
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>new Response(JSON.stringify(url.endsWith('/state') ? {candidate:value,current_status:'review',events:[]} : url.includes('/decisions?') ? [value] : url.includes('/runs/') ? {status:'succeeded'} : []))));
  render(<Decisions />);
  expect(await screen.findByText('20.00%')).toBeTruthy();
  expect(screen.getByText('30.00%')).toBeTruthy();
  expect(screen.getByText('Position allocation')).toBeTruthy();
  expect((screen.getByRole('button',{name:'Approve decision'}) as HTMLButtonElement).disabled).toBe(true);
  expect(screen.getByText(/Uncalibrated, not a probability of profit/).closest('details')?.open).toBe(false);
});
it('requires a reason and persists rejection with exact prior state', async () => {
  const fetch = setup(); const user = userEvent.setup(); render(<Decisions />);
  await user.click(await screen.findByRole('button', {name:'Reject decision'}));
  expect((screen.getByRole('button', {name:'Confirm reject'}) as HTMLButtonElement).disabled).toBe(true);
  await user.type(screen.getByLabelText('Reason'), 'Insufficient evidence');
  await user.click(screen.getByRole('button', {name:'Confirm reject'}));
  await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
  expect(await screen.findByText('Needs review → Rejected')).toBeTruthy();
  const request = fetch.mock.calls.find(([url]) => url.endsWith('/transitions'))!;
  expect(JSON.parse(request[1].body as string)).toMatchObject({action:'reject',expected_status:'review',reason:'Insufficient evidence'});
});
it('does not claim success when backend rejects the transition', async () => {
  setup(true); const user = userEvent.setup(); render(<Decisions />);
  await user.click(await screen.findByRole('button', {name:'Reject decision'}));
  await user.type(screen.getByLabelText('Reason'), 'Insufficient evidence');
  await user.click(screen.getByRole('button', {name:'Confirm reject'}));
  expect((await screen.findByRole('alert')).textContent).toContain('No successful transition');
  expect(screen.getByRole('dialog')).toBeTruthy();
  expect(screen.queryByText('Needs review → Rejected')).toBeNull();
});

it('loads a deep-linked candidate outside the history page instead of substituting the first row', async () => {
  window.history.replaceState(null, '', '#/decisions?decision=older-candidate');
  const fetch = setup(false, {...candidate, decision_id: 'older-candidate'}); render(<Decisions />);
  expect(await screen.findByText(candidate.thesis)).toBeTruthy();
  expect(fetch.mock.calls.some(([url]) => url === '/api/v1/decisions/older-candidate/state')).toBe(true);
});

it('withholds a mismatched deep-link response and never fetches its run', async () => {
  window.history.replaceState(null, '', '#/decisions?decision=older-candidate');
  const fetch = setup(); render(<Decisions />);
  expect((await screen.findByRole('alert')).textContent).toContain('does not match');
  expect(screen.queryByText(candidate.thesis)).toBeNull();
  expect(screen.queryByRole('button', {name:'Reject decision'})).toBeNull();
  expect(fetch.mock.calls.some(([url]) => url.includes('/runs/'))).toBe(false);
});

it.each(['run_id', 'instrument_id', 'analysis_as_of', null])('requires matching research identity before approval: %s', async field => {
  const ready = {...candidate, status:'ready_for_approval', data_quality:'OK', policy_checks:[{check_id:'max_position_weight',policy_id:'p',policy_version:'1',result:'PASS',blocking:true,reason:'Within allocation limit',observed_value:.2,limit_value:.3}]};
  const run = {run_id:candidate.run_id,instrument_id:candidate.instrument_id,analysis_as_of:candidate.as_of,status:'succeeded', ...(field ? {[field]:'mismatched'} : {})};
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>new Response(JSON.stringify(url.endsWith('/state') ? {candidate:ready,current_status:'ready_for_approval',events:[]} : url.includes('/decisions?') ? [ready] : url.includes('/runs/') ? run : []))));
  render(<Decisions />);
  await screen.findByText(field ? 'Matching research status unavailable. Approval remains disabled.' : 'Research processing: Research complete');
  expect((screen.getByRole('button',{name:'Approve decision'}) as HTMLButtonElement).disabled).toBe(field !== null);
});

it('does not substitute another candidate when the deep link is missing or forbidden', async () => {
  window.history.replaceState(null, '', '#/decisions?decision=unavailable-candidate');
  vi.stubGlobal('fetch', vi.fn(async (url: string) => new Response(JSON.stringify(url.includes('/decisions?') ? [candidate] : []),
    { status: url.endsWith('/unavailable-candidate/state') ? 404 : 200 })));
  render(<Decisions />);
  expect(await screen.findByRole('alert')).toBeTruthy();
  expect(screen.queryByText(candidate.thesis)).toBeNull();
  expect(screen.queryByRole('button', {name:'Approve decision'})).toBeNull();
});
