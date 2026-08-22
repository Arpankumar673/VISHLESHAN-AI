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
  [key: string]: any;
  overview?: {
    name?: string;
    summary?: string;
    description?: string;
    industry?: string;
    headquarters?: string;
    official_domain?: string;
    founded?: string;
    size?: string;
    mission?: string;
  };
  executive_intelligence?: {
    summary?: string;
    company_name?: string;
    official_domain?: string;
    trust_score?: number;
    risk_level?: string;
    confidence?: number;
    verified_claims?: number;
    total_claims?: number;
    conflicts_count?: number;
    unable_to_verify_count?: number;
  };
  final_decision_summary?: {
    decision?: string;
    uncertainty_aware?: boolean;
    verdict_label?: string;
  };
  official_resources?: {
    website?: string;
    careers_portal?: string;
    primary_domain?: string;
    contact_email?: string;
    official_channels?: string[];
  };
  domain_provenance?: {
    domain?: string;
    status?: string;
    https_support?: boolean;
    canonical_url?: string;
    summary?: string;
  };
  identity_verification?: {
    status?: VerificationStatus | string;
    domain_verified?: boolean;
    identity_summary?: string;
    summary?: string;
    verified_identifiers?: VerifiedIdentifierItem[] | any[];
  };
  registration_findings?: {
    status?: VerificationStatus | string;
    findings?: RegistrationItem[] | any[];
    summary?: string;
    notes?: string;
  };
  certification_findings?: {
    status?: VerificationStatus | string;
    certifications?: CertificationItem[] | any[];
    summary?: string;
    notes?: string;
  };
  trust_score_explanation?: {
    contributing_signals?: any[];
    explanation?: string;
  };
  risk_score_explanation?: {
    overall_risk?: string;
    factors?: string[];
  };
  recruitment_risk?: {
    company_legitimacy?: string;
    job_offer_risk?: string;
    careers_portal_verified?: boolean;
    indicators?: any[];
  };
  news_hiring?: {
    summary?: string;
    active_hiring_channels?: boolean;
    careers_url?: string;
    recent_events?: NewsEventItem[];
    hiring_signals?: any;
  };
  hiring_intelligence?: {
    careers_url?: string;
    status?: string;
    open_roles_observed?: boolean;
  };
  technology_reputation?: {
    infrastructure?: string;
    tech_stack?: string[];
    engineering_presence?: string;
    public_sentiment?: string;
    signals?: TechnicalSignalItem[];
  };
  reputation_intelligence?: {
    public_sentiment?: string;
    employee_presence_verified?: boolean;
    summary?: string;
  };
  trust_score?: TrustScore | any;
  confidence?: any;
  risk_analysis?: RiskAnalysisResult | any;
  important_conclusions?: string[];
  conflicting_evidence?: any[];
  uncertainty_findings?: any[];
  source_reliability?: any;
  evidence?: Evidence[] | any[];
  references?: ReferenceItem[] | any[];
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
