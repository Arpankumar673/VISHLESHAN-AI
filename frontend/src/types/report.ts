import type { Company } from './company';
import type { Evidence, SourceType, VerificationStatus } from './evidence';
import type { TrustScore } from './trust';
import type { RiskAnalysisResult } from './risk';

export interface VerifiedIdentifierItem {
  type: string;
  value: string;
  status: VerificationStatus;
  source_url: string;
}

export interface RegistrationItem {
  authority: string;
  registration_number?: string;
  jurisdiction?: string;
  status: VerificationStatus;
  source_url: string;
  date?: string;
}

export interface CertificationItem {
  name: string;
  issuer: string;
  validity?: string;
  status: VerificationStatus;
  source_url: string;
}

export interface NewsEventItem {
  title: string;
  date?: string;
  source: string;
  url: string;
  summary: string;
}

export interface TechnicalSignalItem {
  type: string;
  label: string;
  confidence: number;
  source_url?: string;
}

export interface ReferenceItem {
  index: number;
  url: string;
  title: string;
  sourceType: SourceType;
  observedAt: string;
  reliability: number;
}

export interface ReportContent {
  overview?: {
    summary: string;
    industry?: string;
    headquarters?: string;
    founded?: string;
    size?: string;
    mission?: string;
  };
  official_resources?: {
    website?: string;
    careers_portal?: string;
    contact_email?: string;
    official_channels?: string[];
  };
  identity_verification?: {
    status: VerificationStatus;
    domain_verified: boolean;
    identity_summary: string;
    verified_identifiers: VerifiedIdentifierItem[];
  };
  registration_findings?: {
    status: VerificationStatus;
    findings: RegistrationItem[];
    notes?: string;
  };
  certification_findings?: {
    status: VerificationStatus;
    certifications: CertificationItem[];
    notes?: string;
  };
  news_hiring?: {
    recent_events: NewsEventItem[];
    hiring_signals: {
      active_openings?: number;
      hiring_status?: string;
      departments?: string[];
      hiring_notes?: string;
    };
  };
  technology_reputation?: {
    tech_stack?: string[];
    engineering_presence?: string;
    public_sentiment?: string;
    signals: TechnicalSignalItem[];
  };
  trust_score?: TrustScore;
  confidence?: {
    score: number;
    rating: string;
    rationale: string;
  };
  risk_analysis?: RiskAnalysisResult;
  important_conclusions?: string[];
  evidence?: Evidence[];
  references?: ReferenceItem[];
}

export interface Report {
  id: string;
  company_id: string;
  research_run_id: string;
  title: string;
  content: ReportContent;
  report_version: string;
  created_at: string;
  updated_at: string;
  company?: Company;
}
