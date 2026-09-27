const PREFIX = '/api/v1';
export const SESSION_EXPIRED = 'tradingagents:session-expired';

export class ApiError extends Error {
  constructor(public readonly status: number) {
    super(status === 401 ? 'Sign in again to continue.'
      : status === 403 ? 'Request denied. Refresh your session and try again.'
      : status === 409 ? 'The record changed. Refresh before trying again.'
      : status === 422 ? 'Some inputs are invalid. Check the form and try again.'
      : status === 0 ? 'Cannot reach the local API. Check that it is running.'
      : 'The request could not be completed. Try again.');
  }
}

/** All requests stay on this origin. Never reflect unrestricted server errors. */
export async function request<T>(path: string, init: RequestInit = {}, maxBytes?: number): Promise<T> {
  if (!path.startsWith('/') || path.startsWith('//') || path.includes('..')) {
    throw new Error('Invalid API path');
  }
  let response: Response;
  try {
    response = await fetch(`${PREFIX}${path}`, {
      ...init, credentials: 'same-origin', cache: 'no-store', redirect: 'error',
      headers: { Accept: 'application/json', ...init.headers },
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new ApiError(0);
  }
  if (!response.ok) {
    if (response.status === 401 && path !== '/auth/login') {
      window.dispatchEvent(new Event(SESSION_EXPIRED));
    }
    throw new ApiError(response.status);
  }
  try {
    if (maxBytes !== undefined) {
      if (Number(response.headers.get('Content-Length')) > maxBytes || !response.body) {
        await response.body?.cancel();
        throw new ApiError(502);
      }
      const reader = response.body.getReader();
      const chunks: Uint8Array[] = [];
      let size = 0;
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          size += value.byteLength;
          if (size > maxBytes) throw new ApiError(502);
          chunks.push(value);
        }
      } finally { await reader.cancel(); reader.releaseLock(); }
      const bytes = new Uint8Array(size);
      let offset = 0;
      for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
      return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes)) as T;
    }
    return await response.json() as T;
  }
  catch { throw new ApiError(502); }
}

/** Fetch a session-bound token on demand; neither credentials nor reports are persisted. */
export async function mutate<T>(path: string, body?: unknown, method = 'POST', headers = {}, signal?: AbortSignal): Promise<T> {
  const csrf = await request<{ csrf_token: string }>('/auth/csrf', { signal });
  if (typeof csrf.csrf_token !== 'string' || !csrf.csrf_token) throw new ApiError(502);
  return request<T>(path, {
    method, signal, headers: { ...headers, 'Content-Type': 'application/json', 'X-CSRF-Token': csrf.csrf_token },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export interface Owner { owner_id: string; email: string }
export function validateOwner(value: Owner): Owner {
  if (!value || typeof value.owner_id !== 'string' || typeof value.email !== 'string') {
    throw new ApiError(502);
  }
  return { owner_id: value.owner_id, email: value.email };
}
export function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : 'An unexpected error occurred. Try again.';
}
