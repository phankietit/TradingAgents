import { t, useLocale } from './i18n';

export interface ResearchEvent { sequence: number; event_type: string; occurred_at: string; stage?: string; attempt?: number }

/** Real events only. A finished worker is not evidence of a valid conclusion. */
export default function ResearchWorkflow({events, status, hasSources, hasReport}: {
  events: ResearchEvent[]; status: string; hasSources: boolean; hasReport: boolean;
}) {
  useLocale();
  const start = [...events].reverse().find(event => event.event_type === 'run.started')?.sequence ?? 0;
  const latestAttempt = events.reduce((latest, event) => Math.max(latest, event.attempt ?? 0), 0);
  const attempt = events.filter(event => event.sequence >= start && (!latestAttempt || event.attempt === latestAttempt));
  const stages = attempt.filter(event => event.stage && ['stage.started', 'stage.completed'].includes(event.event_type));
  const latest = stages.at(-1);
  const presentation = ['Financial validation', 'Report presentation'].includes(latest?.stage ?? '');
  const stopped = ['failed', 'cancelled'].includes(status);
  const stopping = status === 'cancel_requested';
  const running = status === 'running';
  const steps = [
    {title:'Evidence prepared', detail:hasSources ? 'Saved sources selected' : 'No sources selected', state:hasSources ? 'done' : 'waiting'},
    {title:'Research & challenge', detail:status === 'locally_stopped' ? 'Local processing stopped' : status === 'review_required' ? 'Processing state needs review' : stopping ? 'Stop requested; shutdown not yet verified' : running && !presentation && latest?.stage ? latest.stage : stopped ? 'Processing stopped' : 'Analysts, opposing views and risk review', state:running && !presentation ? 'active' : stages.some(event => event.stage === 'Portfolio Manager' && event.event_type === 'stage.completed') ? 'done' : 'waiting'},
    {title:'Report preparation', detail:hasReport ? 'Saved report available' : presentation ? latest!.stage! : 'Financial checks and presentation', state:hasReport ? 'done' : running && presentation ? 'active' : 'waiting'},
    {title:'Your decision', detail:'Read the findings and limitations', state:hasReport ? 'active' : 'waiting'},
  ];
  return <section className="research-workflow" aria-label={t('Research workflow')}>
    <ol>{steps.map((step, index) => <li key={step.title} className={step.state} aria-current={step.state === 'active' ? 'step' : undefined}>
      <span className="workflow-index" aria-hidden="true">{String(index + 1).padStart(2, '0')}</span>
      <div><strong>{t(step.title)}</strong><span>{t(step.detail)}</span></div>
    </li>)}</ol>
    {hasReport ? <p className="muted caption">{t('Processing is finished. Check the report validation status before using its conclusions.')}</p> : null}
  </section>;
}
