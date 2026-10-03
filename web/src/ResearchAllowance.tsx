import { t, useLocale } from './i18n';

export default function ResearchAllowance({ seconds, onChange, disabled }: {
  seconds: number; onChange: (seconds: number) => void; disabled: boolean;
}) {
  useLocale();
  return <section className="notice" aria-label={t('Research time allowance')}>
    <label>{t('Research time allowance')}<select value={seconds} disabled={disabled}
      onChange={event => onChange(Number(event.target.value))}>
      <option value={1800}>{t('30 minutes · default')}</option>
      <option value={3600}>{t('60 minutes · more time')}</option>
    </select></label>
    <p className="muted">{t('All research steps are preserved. More time may help a slow analysis finish, but does not guarantee a report or cap AI charges.')}</p>
    <p className="muted caption">{t('The time limit is checked between steps. A model request already in progress may continue beyond it and may still incur charges. This is not an exact completion timer.')}</p>
  </section>;
}
