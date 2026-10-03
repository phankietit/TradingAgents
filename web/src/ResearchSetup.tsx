import { t, useLocale } from './i18n';
import { ApiError, errorMessage } from './api';
import { useResource } from './data';

interface Configuration {
  provider: string; quick_model: string; deep_model: string;
  worker_status: 'UNVERIFIED'; provider_connection: 'UNVERIFIED'; max_job_attempts: number;
}
function validate(value: Configuration): Configuration {
  if (!value || ![value.provider, value.quick_model, value.deep_model].every(item => typeof item === 'string' && item.length > 0)
    || value.worker_status !== 'UNVERIFIED' || value.provider_connection !== 'UNVERIFIED'
    || !Number.isInteger(value.max_job_attempts) || value.max_job_attempts < 1 || value.max_job_attempts > 20) throw new ApiError(502);
  return value;
}

export default function ResearchSetup() {
  useLocale();
  const result = useResource<Configuration>('/analysis-configuration', 0, validate);
  return <section aria-label={t("Research service setup")} className="notice">
    <h3>{t("Before you start")}</h3>
    <p>{t("Research runs in a separate background service and may incur model charges. A saved configuration does not confirm that the service is running or that provider access is working.")}</p>
    {result.loading ? <p role="status">{t("Loading research settings…")}</p> : result.error ? <p className="warning">{t("Research settings unavailable.")} {t(errorMessage(result.error))}  {t("Check the local setup before authorizing a run.")}</p> : result.data ? <>
      <p>{t("Service availability and provider connection: not verified. No paid connection test has been made.")}</p>
      <details><summary>{t("Models & processing details")}</summary><dl>
        <dt>{t("Provider")}</dt><dd>{result.data.provider}</dd><dt>{t("Quick analysis model")}</dt><dd>{result.data.quick_model}</dd>
        <dt>{t("Deep analysis model")}</dt><dd>{result.data.deep_model}</dd><dt>{t("Maximum processing attempts")}</dt><dd>{result.data.max_job_attempts}</dd>
      </dl><p>{t("Settings apply to new runs. Check the selected run for its recorded configuration. An automatic retry can incur additional model charges.")}</p></details>
    </> : null}
  </section>;
}
