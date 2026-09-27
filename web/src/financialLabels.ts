export function reviewStatus(value: string): string {
  const labels: Record<string, string> = {review:'Needs review',ready_for_approval:'Ready for your review',approved:'Approved',rejected:'Rejected',superseded:'Superseded',expired:'Expired',draft:'Draft'};
  return Object.hasOwn(labels,value) ? labels[value] : 'Status unavailable';
}
export function qualityLabel(value: string): string {
  const labels: Record<string,string>={OK:'Checks passed',STALE:'Outdated data',NO_DATA:'No data returned',COVERAGE_GAP:'Incomplete historical coverage',INVALID:'Invalid data',UNAVAILABLE:'Data source unavailable'};
  return Object.hasOwn(labels,value) ? labels[value] : 'Quality not verified';
}
export function riskLabel(value: string): string {
  const labels: Record<string,string>={data_quality:'Data quality',tradability:'Eligible investment',max_position_weight:'Position allocation',max_asset_class_weight:'Asset-class allocation',max_gross_exposure:'Total exposure',max_turnover:'Portfolio turnover',max_correlation:'Holding correlation',min_cash_weight:'Cash reserve'};
  return Object.hasOwn(labels,value) ? labels[value] : value.replaceAll('_',' ');
}
export function riskReason(checkId: string, result: string, reason: string): string {
  if (reason !== `${checkId} ${result}`) return reason;
  if (result === 'PASS') return `${riskLabel(checkId)} requirement met`;
  if (result === 'FAIL') return `${riskLabel(checkId)} requirement not met`;
  return reason;
}
export function eventLabel(value: string): string {
  const labels: Record<string,string>={'run.queued':'Waiting to start','run.started':'Research started','stage.started':'Research step started','stage.completed':'Research step completed','artifact.created':'Report saved','decision.ready':'Decision available for review','run.retrying':'Retry scheduled','run.cancel_requested':'Cancellation requested','run.cancelled':'Cancelled','run.failed':'Research failed','run.succeeded':'Research completed'};
  return Object.hasOwn(labels,value) ? labels[value] : 'Processing update';
}
