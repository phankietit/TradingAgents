import { expect, it } from 'vitest';
import { preparedSources } from './preparedSources';
import type { Snapshot } from './data';

const snapshot = (id: string, dataset: string, series?: string) => ({snapshot_id:id,dataset,metadata:{series_id:series}} as Snapshot);
it('replaces headlines without dropping selected macro or unknown sources', () => {
  expect(preparedSources(['macro','old','unknown'], snapshot('new','news'), [snapshot('old','news'),snapshot('macro','macro','DGS10')])).toEqual(['macro','unknown','new']);
});
it('replaces only the same macro series while preserving other indicators and headlines', () => {
  const known=[snapshot('old','macro','DGS10'),snapshot('cpi','macro','CPIAUCSL'),snapshot('news','news')];
  expect(preparedSources(['old','cpi','news'],snapshot('new','macro','DGS10'),known)).toEqual(['cpi','news','new']);
});
it('reusing the selected snapshot never duplicates it', () => {
  const source=snapshot('source','macro','DGS10');
  expect(preparedSources(['source'],source,[source])).toEqual(['source']);
});
it('replaces only the same social vendor while retaining the other feed', () => {
  const old={...snapshot('old','social'),vendor:'stocktwits'};
  const reddit={...snapshot('reddit','social'),vendor:'reddit'};
  expect(preparedSources(['old','reddit','unknown'],{...old,snapshot_id:'new'},[old,reddit])).toEqual(['reddit','unknown','new']);
});
it('requires explicit review at 16 sources instead of silently cutting the list', () => {
  const ids=Array.from({length:16},(_,index)=>String(index));
  expect(preparedSources(ids,snapshot('new','news'),[])).toBeNull();
  expect(preparedSources(ids,snapshot('new','news'),[snapshot('0','news')])).toHaveLength(16);
});
