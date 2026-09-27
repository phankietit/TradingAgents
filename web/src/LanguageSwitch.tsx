import { setLocale, useLocale } from './i18n';

export default function LanguageSwitch() {
  const locale = useLocale();
  return <div className="language-switch" role="group" aria-label="Ngôn ngữ / Language">
    <button type="button" lang="vi" aria-pressed={locale === 'vi'} onClick={() => setLocale('vi')}>VI<span className="language-name"> · Tiếng Việt</span></button>
    <button type="button" lang="en" aria-pressed={locale === 'en'} onClick={() => setLocale('en')}>EN<span className="language-name"> · English</span></button>
  </div>;
}
