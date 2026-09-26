import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, mutate, request, SESSION_EXPIRED, validateOwner } from './api';

afterEach(() => vi.unstubAllGlobals());
describe('same-origin API client', () => {
  it('bootstraps CSRF then sends it only to the API mutation', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({ csrf_token: 'fixture-token' })))
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: 'logged_out' })));
    vi.stubGlobal('fetch', fetch);
    await mutate('/auth/logout');
    expect(fetch.mock.calls[0][0]).toBe('/api/v1/auth/csrf');
    expect(fetch.mock.calls[1][1]).toMatchObject({ credentials: 'same-origin', cache: 'no-store', redirect: 'error',
      method: 'POST', headers: { 'X-CSRF-Token': 'fixture-token' } });
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });
  it('does not reflect server secrets or HTML in errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('private-token <script>bad</script>', { status: 422 })));
    await expect(request('/runs')).rejects.toThrow('Some inputs are invalid');
  });
  it('signals expired sessions but not an incorrect login', async () => {
    const listener = vi.fn();
    window.addEventListener(SESSION_EXPIRED, listener);
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('', { status: 401 })));
    await expect(request('/auth/login')).rejects.toBeInstanceOf(ApiError);
    expect(listener).not.toHaveBeenCalled();
    await expect(request('/runs')).rejects.toBeInstanceOf(ApiError);
    expect(listener).toHaveBeenCalledOnce();
    window.removeEventListener(SESSION_EXPIRED, listener);
  });
  it('never mutates when CSRF bootstrap fails', async () => {
    const fetch = vi.fn().mockResolvedValue(new Response('', { status: 403 }));
    vi.stubGlobal('fetch', fetch);
    await expect(mutate('/runs', {})).rejects.toBeInstanceOf(ApiError);
    expect(fetch).toHaveBeenCalledOnce();
  });
  it('rejects external and parent paths before fetching', async () => {
    const fetch = vi.fn(); vi.stubGlobal('fetch', fetch);
    for (const path of ['https://evil.example', '//evil.example', '/../outside']) {
      await expect(request(path)).rejects.toThrow('Invalid API path');
    }
    expect(fetch).not.toHaveBeenCalled();
  });
  it('rejects malformed owner responses', () => {
    expect(() => validateOwner({ owner_id: 'fixture', email: null } as never)).toThrow(ApiError);
  });
});
