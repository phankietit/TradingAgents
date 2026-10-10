import {render, screen, within} from '@testing-library/react';
import {afterEach, expect, it} from 'vitest';
import ResearchWorkflow, {type ResearchEvent} from './ResearchWorkflow';
import {setLocale} from './i18n';

afterEach(() => setLocale('en'));
it('does not infer shutdown from an uncertain execution requiring review', () => {
  render(<ResearchWorkflow events={[]} status="review_required" hasSources hasReport={false} />);
  expect(screen.getByText('Processing state needs review')).toBeTruthy();
  expect(screen.queryByText('Processing stopped')).toBeNull();
});

const event = (sequence: number, event_type: string, stage?: string): ResearchEvent => ({sequence, event_type, stage, occurred_at:'2026-09-27T07:00:00Z'});
it.each(['en', 'vi'] as const)('does not turn a cancellation request into shutdown proof in %s', locale => {
  setLocale(locale);
  render(<ResearchWorkflow events={[event(1,'stage.started','Bear Researcher')]} status="cancel_requested" hasSources hasReport={false} />);
  expect(screen.getByText(locale === 'en' ? 'Stop requested; shutdown not yet verified' : 'Đã yêu cầu dừng; chưa xác minh xử lý đã dừng')).toBeTruthy();
  expect(screen.queryByText(locale === 'en' ? 'Processing stopped' : 'Đã dừng xử lý')).toBeNull();
  expect(screen.queryByText(/Processing is finished/)).toBeNull();
  expect(screen.queryByRole('progressbar')).toBeNull();
});
it.each(['failed', 'cancelled'])('retains terminal processing text for %s without a report', status => {
  render(<ResearchWorkflow events={[]} status={status} hasSources hasReport={false} />);
  expect(screen.getByText('Processing stopped')).toBeTruthy();
  expect(screen.queryByText('Stop requested; shutdown not yet verified')).toBeNull();
  expect(screen.queryByText(/Processing is finished/)).toBeNull();
});
it('shows the actual active stage without inventing a completion percentage', () => {
  render(<ResearchWorkflow events={[event(1,'run.started'),event(2,'stage.started','Bear Researcher')]} status="running" hasSources hasReport={false} />);
  expect(screen.getByText('Bear Researcher')).toBeTruthy();
  expect(screen.getByText('Research & challenge').closest('li')?.getAttribute('aria-current')).toBe('step');
  expect(screen.queryByRole('progressbar')).toBeNull();
});
it('does not use completed stages from a failed earlier attempt', () => {
  render(<ResearchWorkflow events={[event(1,'stage.completed','Portfolio Manager'),event(2,'run.started')]} status="retry_wait" hasSources hasReport={false} />);
  expect(screen.getByText('Research & challenge').closest('li')?.className).toBe('waiting');
});
it('distinguishes report availability from validated conclusions', () => {
  render(<ResearchWorkflow events={[]} status="succeeded" hasSources hasReport />);
  expect(screen.getByText('Processing is finished. Check the report validation status before using its conclusions.')).toBeTruthy();
  const review = screen.getByText('Your decision').closest('li')!;
  expect(within(review).getByText('Read the findings and limitations')).toBeTruthy();
  expect(screen.queryByText('Approved')).toBeNull();
});
it.each(['queued', 'running', 'retry_wait', 'cancel_requested', 'review_required', 'failed', 'cancelled'])('does not infer finished processing from a saved report while status is %s', status => {
  render(<ResearchWorkflow events={[]} status={status} hasSources hasReport />);
  expect(screen.getByText('Saved report available')).toBeTruthy();
  expect(screen.queryByText('Processing is finished. Check the report validation status before using its conclusions.')).toBeNull();
  expect(screen.getByText('A saved report does not confirm processing has finished. Check status and validation before using conclusions.')).toBeTruthy();
  expect(screen.queryByText('Approved')).toBeNull();
});
it.each(['queued', 'running', 'retry_wait', 'cancel_requested', 'review_required', 'failed', 'cancelled'])('preserves the saved-report/status distinction in Vietnamese for %s', status => {
  setLocale('vi');
  render(<ResearchWorkflow events={[]} status={status} hasSources hasReport />);
  expect(screen.getByText('Báo cáo đã được lưu')).toBeTruthy();
  expect(screen.queryByText('Đã xử lý xong. Hãy kiểm tra trạng thái xác minh báo cáo trước khi sử dụng kết luận.')).toBeNull();
  expect(screen.getByText('Báo cáo đã lưu không chứng minh việc xử lý đã hoàn tất. Hãy kiểm tra trạng thái xử lý và xác minh báo cáo trước khi sử dụng kết luận.')).toBeTruthy();
});
it('updates completion wording only after authoritative status changes to succeeded', () => {
  const view = render(<ResearchWorkflow events={[]} status="running" hasSources hasReport />);
  expect(screen.getByText('A saved report does not confirm processing has finished. Check status and validation before using conclusions.')).toBeTruthy();
  view.rerender(<ResearchWorkflow events={[]} status="succeeded" hasSources hasReport />);
  expect(screen.queryByText('A saved report does not confirm processing has finished. Check status and validation before using conclusions.')).toBeNull();
  expect(screen.getByText('Processing is finished. Check the report validation status before using its conclusions.')).toBeTruthy();
  expect(screen.queryByText('Approved')).toBeNull();
});
it.each(['Bear Researcher', 'Financial validation'])('has only one current processing phase when a report is retained during %s', stage => {
  render(<ResearchWorkflow events={[event(1,'run.started'),event(2,'stage.started',stage)]} status="running" hasSources hasReport />);
  const active = screen.getByRole('region',{name:'Research workflow'}).querySelectorAll('[aria-current="step"]');
  expect(active).toHaveLength(1);
  expect(active[0].textContent).toContain(stage);
  expect(screen.getByText('Your decision').closest('li')?.getAttribute('aria-current')).toBeNull();
});
it('does not assign a current processing phase to a queued job with a retained report', () => {
  render(<ResearchWorkflow events={[]} status="queued" hasSources hasReport />);
  expect(screen.getByRole('region',{name:'Research workflow'}).querySelectorAll('[aria-current="step"]')).toHaveLength(0);
  expect(screen.getByText('Saved report available')).toBeTruthy();
});
it('reads a long linked timeline without an argument-spread limit or discarding the latest stage', () => {
  const events = Array.from({length:150_000},(_,index)=>({...event(index+1,'model.usage'),attempt:2}));
  events.push({...event(150_001,'stage.started','Financial validation'),attempt:2});
  render(<ResearchWorkflow events={events} status="running" hasSources hasReport={false} />);
  expect(screen.getByText('Financial validation')).toBeTruthy();
  expect(screen.getByText('Report preparation').closest('li')?.getAttribute('aria-current')).toBe('step');
  expect(screen.queryByRole('progressbar')).toBeNull();
});
