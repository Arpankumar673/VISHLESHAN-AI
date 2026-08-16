import type { Company } from './company';
import type { TrustScore } from './trust';

export type ResearchStatus =
  | 'queued'
  | 'running'
  | 'completed'
  | 'partial'
  | 'failed';

export interface ResearchRun {
  id: string;
  user_id: string;
  company_id: string;
  status: ResearchStatus;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  company?: Company;
  trust_score?: TrustScore;
}

export interface ResearchAgentStep {
  agentName: string;
  label: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'partial' | 'failed';
  itemsFound?: number;
  message?: string;
}

export interface StartResearchPayload {
  company_name: string;
  company_url?: string;
  deep_verification?: boolean;
}

export interface StartResearchResponse {
  research_run_id: string;
  company_id: string;
  status: ResearchStatus;
}
