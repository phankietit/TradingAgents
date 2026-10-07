import { useEffect, useRef, useState } from 'react';
import { readProgress, type Progress } from './continuationData';

type State = {identity: string; data?: Progress; error?: unknown; loading: boolean};

/** No persistent cache: an execution/attempt change cannot paint prior progress.
 * Failed validation clears both display and cursor, so retry rechecks all pages. */
export function useContinuationProgress(path: string | null, attempt: number, version: number): State {
  const identity = `${path ?? ''}@${attempt}`;
  const cache = useRef<State | null>(null);
  const refresh = useRef<(() => void) | null>(null);
  const [state, setState] = useState<State>({identity, loading:!!path});
  useEffect(() => {
    if (!path) return;
    const controller = new AbortController();
    let reading = false;
    let again = false;
    const read = async () => {
      if (reading) { again = true; return; }
      reading = true;
      do {
        again = false;
        const prior = cache.current?.identity === identity ? cache.current.data : undefined;
        setState({identity, data:prior, loading:true});
        try {
          const data = await readProgress(path, attempt, controller.signal, prior?.events);
          if (controller.signal.aborted) return;
          cache.current = {identity, data, loading:false};
          setState(cache.current);
        } catch (error) {
          if (controller.signal.aborted) return;
          cache.current = null;
          setState({identity, error, loading:false});
        }
      } while (again && !controller.signal.aborted);
      reading = false;
    };
    refresh.current = read;
    return () => { controller.abort(); refresh.current = null; };
  }, [path, attempt, identity]);
  // Coalesce polling while reading rather than aborting a long paginated read
  // every five seconds. Only identity changes/unmount abort in-flight work.
  useEffect(() => { refresh.current?.(); }, [version, identity]);
  return path && state.identity === identity ? state : {identity, loading:!!path};
}
