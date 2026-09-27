import { useSyncExternalStore } from 'react';
import { vietnamese } from './messages';

export type Locale = 'en' | 'vi';
const key = 'tradingagents.ui-language.v1';
const listeners = new Set<() => void>();
function initialLocale(): Locale {
  try {
    const saved = localStorage.getItem(key);
    if (saved === 'en' || saved === 'vi') return saved;
  } catch { /* Storage may be disabled; language still works in memory. */ }
  return navigator.language.toLowerCase().startsWith('vi') ? 'vi' : 'en';
}
let locale: Locale = initialLocale();
export function setLocale(value: Locale) {
  if (value !== 'en' && value !== 'vi') return;
  locale = value;
  document.documentElement.lang = value;
  try { localStorage.setItem(key, value); } catch { /* No private data is stored. */ }
  listeners.forEach(listener => listener());
}
function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}
export function useLocale() {
  return useSyncExternalStore(subscribe, () => locale, () => 'en' as Locale);
}
/** Translate application-owned labels only, never arbitrary report/source text. */
export function t(english: string): string {
  if (locale === 'en') return english;
  const trimmed = english.trim();
  if (!Object.hasOwn(vietnamese, trimmed)) return english;
  return english.replace(trimmed, () => vietnamese[trimmed]);
}
export const formatLocale = () => locale === 'vi' ? 'vi-VN' : 'en-US';
document.documentElement.lang = locale;
