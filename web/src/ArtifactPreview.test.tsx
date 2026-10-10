import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import ArtifactPreview from './ArtifactPreview';
import type { Artifact } from './ArtifactPreview';
import { request } from './api';
import { setLocale } from './i18n';

afterEach(() => vi.unstubAllGlobals());
const artifact: Artifact = { artifact_id: 'artifact-fixture', kind: 'analysis_report', media_type: 'application/json',
  byte_size: 500, content_hash: 'sha256:fixture', created_at: '2026-09-01T00:00:00Z' };
const report = { run_id: 'run-fixture', decision_id: '12345678-1234-1234-1234-123456789abc', profile: 'equity',
  reference_only: false, selected_analysts: ['market'], snapshot_attestation: 'PASS', narrative: '<img src=x onerror=alert(1)>', structured_narrative: { thesis: '<script>not executable</script>' } };

it.each([
  {content_hash:'sha256:changed'}, {byte_size:501},
  {created_at:'2026-09-02T00:00:00Z'}, {kind:'decision_evidence'},
])('withdraws the old preview immediately when manifest identity changes %j', async patch => {
  setLocale('en');
  let resolve!: (response:Response)=>void;
  const pending=new Promise<Response>(done=>{resolve=done;});
  const fetch=vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({...report,narrative:'Previous saved content'})))
    .mockReturnValueOnce(pending);
  vi.stubGlobal('fetch',fetch);
  const view=render(<ArtifactPreview artifact={artifact} runId="run-fixture" defaultOpen />);
  await screen.findByText('Previous saved content');
  view.rerender(<ArtifactPreview artifact={{...artifact,...patch}} runId="run-fixture" defaultOpen />);
  expect(screen.queryByText('Previous saved content')).toBeNull();
  expect(screen.queryByRole('link')).toBeNull();
  expect(screen.getByRole('status').textContent).toContain('Loading saved report');
  await act(async()=>resolve(new Response('{}',{status:409})));
  expect((await screen.findByRole('alert')).textContent).toContain('No report contents are shown');
});

it('keeps an in-flight immutable preview across identical metadata object copies', async()=>{
  setLocale('en');
  let resolve!:(response:Response)=>void;
  const pending=new Promise<Response>(done=>{resolve=done;});
  const fetch=vi.fn(()=>pending);vi.stubGlobal('fetch',fetch);
  const view=render(<ArtifactPreview artifact={artifact} runId="run-fixture" defaultOpen />);
  const signal=(fetch.mock.calls[0] as unknown as [string,RequestInit])[1].signal!;
  for(let index=0;index<4;index++)view.rerender(<ArtifactPreview artifact={{...artifact}} runId="run-fixture" defaultOpen />);
  expect(signal.aborted).toBe(false);
  expect(fetch).toHaveBeenCalledTimes(1);
  await act(async()=>resolve(new Response(JSON.stringify({...report,narrative:'Immutable saved content'}))));
  await screen.findByText('Immutable saved content');
  view.rerender(<ArtifactPreview artifact={{...artifact}} runId="run-fixture" defaultOpen />);
  expect(fetch).toHaveBeenCalledTimes(1);
});

it('ignores late bytes from the previous manifest after the new preview succeeds', async()=>{
  setLocale('en');
  let resolve!:(response:Response)=>void;
  const pending=new Promise<Response>(done=>{resolve=done;});
  const fetch=vi.fn().mockReturnValueOnce(pending)
    .mockResolvedValueOnce(new Response(JSON.stringify({...report,narrative:'Current saved content'})));
  vi.stubGlobal('fetch',fetch);
  const view=render(<ArtifactPreview artifact={artifact} runId="run-fixture" defaultOpen />);
  const signal=fetch.mock.calls[0][1].signal;
  view.rerender(<ArtifactPreview artifact={{...artifact,content_hash:'sha256:next'}} runId="run-fixture" defaultOpen />);
  expect(signal.aborted).toBe(true);
  await screen.findByText('Current saved content');
  await act(async()=>resolve(new Response(JSON.stringify({...report,narrative:'Late old content'}))));
  expect(screen.queryByText('Late old content')).toBeNull();
  expect(screen.getByText('Current saved content')).toBeTruthy();
});

const note = { schema_version: '1.0', run_id: 'run-fixture', stage: 'Market Analyst', attempt: 1,
  sequence: 1, analysis_as_of: '2026-09-01T00:00:00Z', research_quality: 'unvalidated',
  approval_eligible: false, sections: {market_report: 'Saved **-22.94%** <img src=x onerror=alert(1)>'} };
it('reads a stage only on demand, never offers approval and never translates original text', async () => {
  setLocale('en');
  const fetch = vi.fn(async () => new Response(JSON.stringify(note))); vi.stubGlobal('fetch', fetch);
  render(<ArtifactPreview artifact={{...artifact, kind:'research_stage'}} runId="run-fixture" />);
  expect(fetch).not.toHaveBeenCalled();
  await userEvent.setup().click(screen.getByRole('button', {name:'Inspect research stage'}));
  expect(await screen.findByText('Unvalidated working note')).toBeTruthy();
  expect(screen.getByText('-22.94%')).toBeTruthy();
  expect(screen.queryByRole('link')).toBeNull(); expect(document.querySelector('img')).toBeNull();
  act(() => setLocale('vi'));
  expect(screen.getByText('Bản nháp chưa kiểm chứng')).toBeTruthy();
  expect(screen.getByText('-22.94%')).toBeTruthy(); expect(fetch).toHaveBeenCalledTimes(1);
  act(() => setLocale('en'));
});
it.each([
  {approval_eligible:true}, {research_quality:'validated'}, {run_id:'other-run'},
  {stage:'Unknown role'}, {sequence:0}, {attempt:0}, {analysis_as_of:'invalid'},
  {sections:{target_weight:'0.5'}}, {sections:{}}, {sections:{market_report:42}},
])('withholds malformed working-note contents %j', async patch => {
  setLocale('en');
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({...note,...patch}))));
  render(<ArtifactPreview artifact={{...artifact,kind:'research_stage'}} runId="run-fixture" defaultOpen />);
  expect((await screen.findByRole('alert')).textContent).toContain('No report contents are shown');
  expect(screen.queryByText('-22.94%')).toBeNull(); expect(screen.queryByRole('link')).toBeNull();
});

it('switches saved bilingual reports without network calls or changing numbers', async () => {
  setLocale('en');
  const fetch = vi.fn(async () => new Response(JSON.stringify({...report, report_language:'en-vi',
    localized_report:{en:'Return **-22.94%**',vi:'Lợi suất **-22.94%**'}})));
  vi.stubGlobal('fetch',fetch);
  render(<ArtifactPreview artifact={artifact} runId="run-fixture" defaultOpen />);
  expect(await screen.findByText('Return', {exact:false})).toBeTruthy();
  const calls = fetch.mock.calls.length;
  act(() => setLocale('vi'));
  expect(screen.getByText('Lợi suất', {exact:false})).toBeTruthy();
  expect(screen.getByText('-22.94%')).toBeTruthy();
  expect(fetch.mock.calls.length).toBe(calls);
  act(() => setLocale('en'));
});

it('loads only on demand and displays untrusted report text plus a bound decision link', async () => {
  const fetch = vi.fn(async () => new Response(JSON.stringify(report)));
  vi.stubGlobal('fetch', fetch);
  const user = userEvent.setup(); render(<ArtifactPreview artifact={artifact} runId="run-fixture" />);
  expect(fetch).not.toHaveBeenCalled();
  await user.click(screen.getByRole('button', { name: 'Inspect analysis report' }));
  expect(await screen.findByText(report.narrative)).toBeTruthy();
  expect(document.querySelector('img')).toBeNull();
  expect(screen.getByRole('link', { name: 'Review linked decision' }).getAttribute('href')).toBe(`#/decisions?decision=${report.decision_id}`);
  await user.click(screen.getByRole('button', { name: 'Verification' }));
  await user.click(screen.getByText('Structured research output'));
  expect(document.querySelector('script')).toBeNull();
  await user.click(screen.getByRole('button', { name: 'Close analysis report' }));
  expect(screen.queryByText(report.narrative)).toBeNull();
});

it('omits only the self-navigation on a decision page, retaining the saved report and verification', async () => {
  setLocale('en');
  const fetch = vi.fn(async () => new Response(JSON.stringify(report)));
  vi.stubGlobal('fetch', fetch);
  render(<ArtifactPreview artifact={artifact} runId="run-fixture" embedded showDecisionLink={false} />);
  expect(await screen.findByText(report.narrative)).toBeTruthy();
  expect(screen.queryByRole('link', {name:'Review linked decision'})).toBeNull();
  expect(screen.getByRole('button', {name:'Verification'})).toBeTruthy();
  expect(fetch).toHaveBeenCalledTimes(1);
});

it('presents validated bilingual sections as a readable brief without altering saved text', async () => {
  setLocale('en');
  const en = '## Executive summary\nBalanced outlook.\n\n## Investment thesis\nSaved evidence **-22.94%**.\n\n## Risks\n- Rival case.\n\n## Invalidation conditions\n- If filing changes.';
  const vietnamese = '## Tóm tắt\nGóc nhìn cân bằng.\n\n## Luận điểm đầu tư\nCăn cứ đã lưu **-22.94%**.\n\n## Rủi ro\n- Luận điểm đối lập.\n\n## Điều kiện mất hiệu lực\n- Nếu báo cáo thay đổi.';
  const fetch = vi.fn(async () => new Response(JSON.stringify({...report,
    structured_narrative:{rating:'Hold'}, validation_issues:[], localized_report:{en,vi:vietnamese},
    coverage:{missing:['news','social']}, report_language:'en-vi'})));
  vi.stubGlobal('fetch', fetch);
  render(<ArtifactPreview artifact={artifact} runId="run-fixture" defaultOpen />);
  expect(await screen.findByRole('heading',{name:'Executive summary',level:4})).toBeTruthy();
  expect(screen.getAllByText('Saved evidence', {exact:false})).toHaveLength(2);
  expect(screen.getByText(/Not covered in this run:/)).toBeTruthy();
  expect(screen.getByText('Read the complete saved report')).toBeTruthy();
  const calls = fetch.mock.calls.length;
  act(() => setLocale('vi'));
  expect(screen.getByRole('heading',{name:'Tóm tắt',level:4})).toBeTruthy();
  expect(screen.getAllByText('Căn cứ đã lưu', {exact:false})).toHaveLength(2);
  expect(fetch.mock.calls.length).toBe(calls);
  act(() => setLocale('en'));
});

it.each(['wrong_run', 'invalid_schema', 'integrity_failure', 'invalid_json'] as const)('withholds preview on %s', async caseName => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(caseName === 'invalid_json' ? '<html>not json</html>' : JSON.stringify(
    { ...report, ...(caseName === 'wrong_run' ? { run_id: 'other-run' } : caseName === 'invalid_schema' ? { narrative: {} } : {}) }),
    { status: caseName === 'integrity_failure' ? 409 : 200 })));
  const user = userEvent.setup(); render(<ArtifactPreview artifact={artifact} runId="run-fixture" />);
  await user.click(screen.getByRole('button', { name: 'Inspect analysis report' }));
  expect((await screen.findByRole('alert')).textContent).toContain('No report contents are shown');
  expect(screen.queryByRole('link')).toBeNull();
});

it('refuses unsupported formats and large manifest sizes without fetching', () => {
  const fetch = vi.fn(); vi.stubGlobal('fetch', fetch);
  const view = render(<ArtifactPreview artifact={{ ...artifact, media_type: 'text/html' }} runId="run-fixture" />);
  expect(screen.queryByRole('button')).toBeNull();
  view.rerender(<ArtifactPreview artifact={{ ...artifact, byte_size: 1_000_001 }} runId="run-fixture" />);
  expect(screen.queryByRole('button')).toBeNull();
  expect(fetch).not.toHaveBeenCalled();
});

it('bounds streamed response bytes even without a content-length header', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ text: 'x'.repeat(50) }))));
  await expect(request('/artifacts/fixture', {}, 20)).rejects.toMatchObject({ status: 502 });
});

it('renders linked evidence provenance and refuses broken graph links', async () => {
  let broken = false;
  const graph = { graph_id: artifact.artifact_id, run_id: report.run_id, as_of: artifact.created_at,
    claims: [{ claim_id: 'claim', claim: 'Synthetic claim', evidence_ids: ['source'] }],
    evidence: [{ evidence_id: 'source', snapshot_id: 'snapshot', claim: 'Synthetic claim', source_name: 'SYNTHETIC QA', content_hash: 'sha256:fixture', source_at: artifact.created_at, observed_at: artifact.created_at }] };
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ ...graph, evidence: broken ? [] : graph.evidence }))));
  const user = userEvent.setup(); render(<ArtifactPreview artifact={{ ...artifact, kind: 'decision_evidence' }} runId="run-fixture" />);
  await user.click(screen.getByRole('button', { name: 'Inspect decision evidence' }));
  await user.click(await screen.findByText('Synthetic claim'));
  expect(screen.getByText('SYNTHETIC QA')).toBeTruthy();
  expect(screen.getByText('snapshot')).toBeTruthy();
  await user.click(screen.getByRole('button', { name: 'Close decision evidence' })); broken = true;
  await user.click(screen.getByRole('button', { name: 'Inspect decision evidence' }));
  await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('Preview unavailable'));
  expect(screen.queryByText('Synthetic claim')).toBeNull();
});
