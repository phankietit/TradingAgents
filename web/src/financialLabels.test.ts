import { expect, it } from 'vitest';
import { eventLabel, qualityLabel, reviewStatus, riskLabel } from './financialLabels';

it('preserves six distinct data-health meanings and fails closed for unknown values',()=>{
  const states=['OK','NO_DATA','STALE','COVERAGE_GAP','INVALID','UNAVAILABLE'];
  expect(new Set(states.map(qualityLabel)).size).toBe(6);
  expect(qualityLabel('unknown')).toBe('Quality not verified');
  expect(qualityLabel('__proto__')).toBe('Quality not verified');
});
it('separates review readiness from approval and translates processing/risk labels only',()=>{
  expect(reviewStatus('ready_for_approval')).toBe('Ready for your review');
  expect(reviewStatus('approved')).toBe('Approved');
  expect(reviewStatus('unknown')).toBe('Status unavailable');
  expect(riskLabel('max_position_weight')).toBe('Position allocation');
  expect(eventLabel('run.succeeded')).toBe('Research completed');
});
