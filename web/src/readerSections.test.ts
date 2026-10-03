import { expect, it } from 'vitest';
import { readerSections } from './readerSections';

it('keeps each application-owned section and its numbers unchanged', () => {
  const text = '## Executive summary\nBalance is uncertain.\n\n## Investment thesis\nEvidence **-22.94%**.\n\n## Risks\n- Rival case.\n\n## Invalidation conditions\n- If filing changes.\n\n## Research horizon\nMedium term.';
  expect(readerSections(text, 'en')).toEqual({summary:'Balance is uncertain.', thesis:'Evidence **-22.94%**.',
    risks:'- Rival case.', invalidation:'- If filing changes.', horizon:'Medium term.'});
  expect(readerSections(text.replace('Executive summary','Tóm tắt').replace('Investment thesis','Luận điểm đầu tư')
    .replace('Risks','Rủi ro').replace('Invalidation conditions','Điều kiện mất hiệu lực')
    .replace('Research horizon','Khung thời gian nghiên cứu'), 'vi')?.thesis).toBe('Evidence **-22.94%**.');
});

it('falls back for unknown headings or model-inserted structure', () => {
  expect(readerSections('## Executive summary\nA', 'en')).toBeNull();
  expect(readerSections('Preamble\n## Executive summary\nA\n## Investment thesis\nB\n## Risks\nC\n## Invalidation conditions\nD', 'en')).toBeNull();
  expect(readerSections('## Executive summary\nA\n## Investment thesis\nB\n## Risks\nC\n## Invalidation conditions\nD\n## Surprise\nE', 'en')).toBeNull();
});
