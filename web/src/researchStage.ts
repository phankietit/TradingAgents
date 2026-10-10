import { ApiError } from './api';

const fields: Record<string, string[]> = {
  'Market Analyst': ['market_report'], 'Sentiment Analyst': ['sentiment_report'],
  'News Analyst': ['news_report'], 'Fundamentals Analyst': ['fundamentals_report'],
  'Bull Researcher': ['argument'], 'Bear Researcher': ['argument'],
  'Research Manager': ['investment_plan'], 'Trader': ['trader_investment_plan'],
  'Aggressive Analyst': ['argument'], 'Conservative Analyst': ['argument'],
  'Neutral Analyst': ['argument'], 'Portfolio Manager': ['research_conclusion'],
  'Financial validation': ['research_conclusion'], 'Report presentation': ['report_en', 'report_vi'],
};
export interface ResearchStage { stage: string; attempt: number; sequence: number; asOf: string; sections: Record<string, string> }
export function researchStage(value: unknown, runId: string): ResearchStage {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new ApiError(502);
  const data = value as Record<string, unknown>;
  if (data.schema_version !== '1.0' || data.run_id !== runId || data.research_quality !== 'unvalidated'
      || data.approval_eligible !== false || typeof data.stage !== 'string' || !Object.hasOwn(fields, data.stage)
      || !Number.isSafeInteger(data.attempt) || Number(data.attempt) < 1
      || !Number.isSafeInteger(data.sequence) || Number(data.sequence) < 1
      || typeof data.analysis_as_of !== 'string' || !Number.isFinite(Date.parse(data.analysis_as_of))
      || !data.sections || typeof data.sections !== 'object' || Array.isArray(data.sections)) throw new ApiError(502);
  const entries = Object.entries(data.sections);
  if (!entries.length || entries.length > 2 || entries.some(([key, text]) => !fields[data.stage as string].includes(key)
      || typeof text !== 'string' || !text.trim() || text.length > 1_000_000)) throw new ApiError(502);
  return { stage: data.stage, attempt: Number(data.attempt), sequence: Number(data.sequence),
    asOf: data.analysis_as_of, sections: data.sections as Record<string, string> };
}
