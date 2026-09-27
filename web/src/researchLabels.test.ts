import { expect, it } from 'vitest';
import { datasetLabel, researchLabel } from './researchLabels';

it('uses display names without inventing unknown source or research meanings', () => {
  expect(researchLabel('market')).toBe('Price & trend');
  expect(researchLabel('__proto__')).toBe('__proto__');
  expect(researchLabel('unknown')).toBe('unknown');
  expect(datasetLabel('ohlcv.daily')).toBe('Daily prices & volume');
  expect(datasetLabel('vendor.custom')).toBe('vendor.custom');
});
