import type { VerificationStatus } from './evidence';

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical' | 'unknown';

export interface TrustScore {
  id?: string;
  company_id: string;
  research_run_id: string;
  score: number;
  confidence: number;
  risk_level: RiskLevel;
  evidence_coverage: number;
  algorithm_version: string;
  explanation?: string | null;
  created_at?: string;
}

export interface TrustSignalBreakdown {
  dimension: string;
  label: string;
  score: number;
  maxScore: number;
  weight: number;
  status: VerificationStatus;
  description: string;
}
