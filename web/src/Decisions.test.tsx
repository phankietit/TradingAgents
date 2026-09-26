import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import Decisions from './Decisions';
import type { Decision } from './Decisions';
const candidate: Decision = { decision_id: 'decision-fixture', run_id: 'run-fixture', instrument_id: 'aapl', as_of: '2026-09-01T00:00:00Z', status: 'review', rating: 'Review', confidence: .5, thesis: '<script>not executable</script>', risks: ['Synthetic risk'], invalidation_conditions: ['Synthetic invalidation'], data_quality: 'STALE', current_weight: null, target_weight: null, max_allowed_weight: null, portfolio_snapshot_id: null, policy_checks: [], evidence: [] };
beforeEach(() => {
  HTMLDialogElement.prototype.showModal = function() { this.setAttribute('open', ''); };
  HTMLDialogElement.prototype.close = function() { this.removeAttribute('open'); };
});
afterEach(() => vi.unstubAllGlobals());
function setup(rejectFails = false) {
  let rejected = false;
  const fetch = vi.fn(async (url: string, init: RequestInit) => {
    const state = { candidate, current_status: rejected ? 'rejected' : 'review', events: rejected ? [{ event_id: 'event', from_status: 'review', to_status: 'rejected', actor_type: 'owner', occurred_at: candidate.as_of, reason: 'Insufficient evidence' }] : [] };
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
it('requires a reason and persists rejection with exact prior state', async () => {
  const fetch = setup(); const user = userEvent.setup(); render(<Decisions />);
  await user.click(await screen.findByRole('button', {name:'Reject decision'}));
  expect((screen.getByRole('button', {name:'Confirm reject'}) as HTMLButtonElement).disabled).toBe(true);
  await user.type(screen.getByLabelText('Reason'), 'Insufficient evidence');
  await user.click(screen.getByRole('button', {name:'Confirm reject'}));
  await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
  expect(await screen.findByText('review → rejected')).toBeTruthy();
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
  expect(screen.queryByText('review → rejected')).toBeNull();
});
