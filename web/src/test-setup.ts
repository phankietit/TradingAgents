import { cleanup } from '@testing-library/react';
import { afterEach, beforeEach } from 'vitest';
import { setLocale } from './i18n';
beforeEach(() => { setLocale('en'); localStorage.clear(); });
afterEach(cleanup);
