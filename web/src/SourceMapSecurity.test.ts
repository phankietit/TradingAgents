import { expect, it } from 'vitest';
import { SourceMapConsumer } from 'source-map-js';

const basic = { version: 3, sources: ['input.js'], names: [], mappings: 'AAAA' };
const indexed = (line: unknown, column: unknown = 0, map: unknown = basic) => ({
  version: 3, sections: [{ offset: { line, column }, map }],
});
// The package declarations only describe flat maps, while its parser accepts
// indexed maps and untrusted objects; exercise that runtime boundary explicitly.
const consume = (map: unknown) => new SourceMapConsumer(
  map as ConstructorParameters<typeof SourceMapConsumer>[0],
);
// Constructor-only probes are bounded even on the old vulnerable package.
// Never serialize huge accepted offsets just to reproduce event-loop exhaustion.
it.each([
  ['oversized line', indexed(10_000_001)],
  ['nested cumulative offset', indexed(6_000_000, 0, indexed(6_000_000))],
  ['string line', indexed('2')],
  ['fractional line', indexed(1.5)],
  ['negative line', indexed(-1)],
  ['non-finite line', indexed(Infinity)],
  ['NaN line', indexed(NaN)],
  ['unsafe integer', indexed(Number.MAX_SAFE_INTEGER + 1)],
  ['string column', indexed(0, '2')],
  ['negative column', indexed(0, -1)],
])('rejects %s before source-map expansion', (_name, map) => {
  expect(() => consume(map)).toThrow();
});

it('preserves ordinary indexed source mapping without truncation', () => {
  const rows: unknown[] = [];
  consume(indexed(2)).eachMapping(row => rows.push(row));
  expect(rows).toEqual([{ source: 'input.js', generatedLine: 3, generatedColumn: 0,
    originalLine: 1, originalColumn: 0, name: null }]);
});
