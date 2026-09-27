import {render, screen, within} from '@testing-library/react';
import {expect, it} from 'vitest';
import ResearchWorkflow, {type ResearchEvent} from './ResearchWorkflow';

const event = (sequence: number, event_type: string, stage?: string): ResearchEvent => ({sequence, event_type, stage, occurred_at:'2026-09-27T07:00:00Z'});
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
