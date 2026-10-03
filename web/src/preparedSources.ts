import type { Snapshot } from './data';

/** Replace the same dataset/series/feed only; unknown and other sources stay visible.
 * Null means explicit review is required, never silently truncate at the limit.
 */
export function preparedSources(ids: string[], incoming: Snapshot, known: Snapshot[]): string[] | null {
  const retained = ids.filter(id => {
    if (id === incoming.snapshot_id) return false;
    const existing = known.find(source => source.snapshot_id === id);
    if (!existing || existing.dataset !== incoming.dataset) return true;
    if (incoming.dataset === 'social') return existing.vendor !== incoming.vendor;
    return incoming.dataset === 'macro' && (!incoming.metadata?.series_id
      || existing.metadata?.series_id !== incoming.metadata.series_id);
  });
  const next = [...retained, incoming.snapshot_id];
  return next.length <= 16 ? next : null;
}
