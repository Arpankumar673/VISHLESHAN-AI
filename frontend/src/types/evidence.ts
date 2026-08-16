export type VerificationStatus =
  | 'verified'
  | 'unverified'
  | 'conflicting'
  | 'unable_to_verify';

export type SourceType =
  | 'government'
  | 'regulator'
  | 'certification_body'
  | 'official_company'
  | 'official_careers'
  | 'official_announcement'
  | 'news'
  | 'professional_network'
  | 'employee_review'
  | 'forum'
  | 'blog'
  | 'other';

export interface Evidence {
  id: string;
  company_id: string;
  research_run_id: string;
  claim: string;
  evidence_text: string;
  source_url: string;
  source_title?: string | null;
  source_type: SourceType;
  published_at?: string | null;
  observed_at: string;
  reliability_score?: number | null;
  confidence_score?: number | null;
  verification_status: VerificationStatus;
  agent_name?: string | null;
  content_hash?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface SourceReliabilityTier {
  tier: 1 | 2 | 3 | 4 | 5;
  label: string;
  description: string;
  baseScore: number;
}
