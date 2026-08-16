import type { RiskLevel } from './trust';

export interface RiskIndicator {
  id: string;
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  evidence_ids?: string[];
  flagged_at?: string;
}

export interface RiskAnalysisResult {
  risk_level: RiskLevel;
  risk_score: number;
  confidence: number;
  indicators: RiskIndicator[];
  supporting_evidence: string[];
  explanation?: string;
}
