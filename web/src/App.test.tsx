import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import App from './App';
import { SESSION_EXPIRED } from './api';

const owner = { owner_id: 'fixture-owner', email: 'owner@example.com' };
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
afterEach(() => { vi.unstubAllGlobals(); window.location.hash = ''; });

it('restores a session, navigates and clears private views on expiry', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(json(owner)));
  render(<App />);
  expect(await screen.findByText(owner.email)).toBeTruthy();
  fireEvent.click(screen.getByRole('link', { name: 'Portfolio' }));
  expect(await screen.findByRole('heading', { name: 'Portfolio' })).toBeTruthy();
  act(() => window.dispatchEvent(new Event(SESSION_EXPIRED)));
  expect(await screen.findByRole('button', { name: 'Sign in' })).toBeTruthy();
  expect(screen.queryByText(owner.email)).toBeNull();
});

it('signs in with entered credentials and signs out through CSRF bootstrap', async () => {
  const fetch = vi.fn().mockResolvedValueOnce(json({}, 401)).mockResolvedValueOnce(json(owner))
    .mockResolvedValueOnce(json({ csrf_token: 'fixture-token' })).mockResolvedValueOnce(json({ status: 'logged_out' }));
  vi.stubGlobal('fetch', fetch);
  const user = userEvent.setup(); render(<App />);
  await screen.findByRole('button', { name: 'Sign in' });
  await user.type(screen.getByLabelText('Owner email'), owner.email);
  await user.type(screen.getByLabelText('Password'), 'synthetic-test-password');
  await user.click(screen.getByRole('button', { name: 'Sign in' }));
  expect(await screen.findByText(owner.email)).toBeTruthy();
  expect(JSON.parse(fetch.mock.calls[1][1].body)).toEqual({ email: owner.email, password: 'synthetic-test-password' });
  await user.click(screen.getByRole('button', { name: 'Sign out' }));
  expect(await screen.findByRole('button', { name: 'Sign in' })).toBeTruthy();
  expect(screen.queryByText(owner.email)).toBeNull();
});

it('clears the password and reports a safe invalid-login message', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(json({ detail: 'never reflect this' }, 401)));
  const user = userEvent.setup(); render(<App />);
  await screen.findByRole('button', { name: 'Sign in' });
  await user.type(screen.getByLabelText('Owner email'), owner.email);
  await user.type(screen.getByLabelText('Password'), 'synthetic-test-password');
  await user.click(screen.getByRole('button', { name: 'Sign in' }));
  expect((await screen.findByRole('alert')).textContent).toBe('Email or password is incorrect.');
  expect((screen.getByLabelText('Password') as HTMLInputElement).value).toBe('');
});

it('keeps the owner signed in when logout fails and exposes retry', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(json(owner)).mockResolvedValueOnce(json({}, 503)));
  const user = userEvent.setup(); render(<App />);
  await user.click(await screen.findByRole('button', { name: 'Sign out' }));
  await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('could not be completed'));
  expect(screen.getByText(owner.email)).toBeTruthy();
  expect((screen.getByRole('button', { name: 'Sign out' }) as HTMLButtonElement).disabled).toBe(false);
});
