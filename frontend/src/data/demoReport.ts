import type { Report } from '../types';

export const DEMO_GOOGLE_REPORT: Report = {
  id: 'demo-google-report-id',
  company_id: 'demo-google-company-id',
  research_run_id: 'demo-google-run-id',
  title: 'Company Intelligence Report — Google LLC',
  report_version: '1.0',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  company: {
    id: 'demo-google-company-id',
    name: 'Google LLC',
    normalized_name: 'google',
    official_domain: 'google.com',
    description:
      'American multinational technology company focusing on artificial intelligence, search engine technology, online advertising, cloud computing, computer software, quantum computing, e-commerce, and consumer electronics.',
    industry: 'Technology / Internet & Artificial Intelligence',
    headquarters: 'Mountain View, California, United States',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  content: {
    overview: {
      name: 'Google LLC',
      summary:
        'Google LLC is a verified global technology leader with multi-layered corporate governance, active public regulatory filings, authentic domain ownership (google.com), and robust engineering infrastructure.',
      description:
        'American multinational technology company focusing on artificial intelligence, search engine technology, online advertising, cloud computing, software, quantum computing, and consumer electronics.',
      industry: 'Technology / Software / AI',
      headquarters: '1600 Amphitheatre Parkway, Mountain View, CA 94043, USA',
      official_domain: 'google.com',
      founded: '1998',
      size: '100,000+ employees',
      mission: "To organize the world's information and make it universally accessible and useful.",
    },
    executive_intelligence: {
      summary:
        'High-confidence verification completed across corporate registry, domain provenance, engineering footprint, and public sentiment. Zero recruitment fraud risk detected.',
      company_name: 'Google LLC',
      official_domain: 'google.com',
      trust_score: 96,
      risk_level: 'low',
      confidence: 0.98,
      verified_claims: 28,
      total_claims: 28,
      conflicts_count: 0,
      unable_to_verify_count: 0,
    },
    final_decision_summary: {
      decision: 'VERIFIED_LEGITIMATE_CORPORATION',
      uncertainty_aware: true,
      verdict_label: 'Verified Corporate Entity — High Trust',
    },
    official_resources: {
      website: 'https://google.com',
      careers_portal: 'https://careers.google.com',
      primary_domain: 'google.com',
      contact_email: 'press@google.com',
      official_channels: [
        'google.com',
        'careers.google.com',
        'blog.google',
        'cloud.google.com',
      ],
    },
    domain_provenance: {
      domain: 'google.com',
      status: 'verified_active',
      https_support: true,
      canonical_url: 'https://www.google.com',
      summary:
        'Domain created in September 1997. Registered under MarkMonitor Inc. DNS records pass SPF, DKIM, and DMARC strict validation.',
    },
    identity_verification: {
      status: 'verified',
      domain_verified: true,
      identity_summary:
        'Confirmed subsidiary of Alphabet Inc. (NASDAQ: GOOGL). Corporate identity verified via SEC EDGAR, Delaware Division of Corporations, and WHOIS domain ownership.',
      summary:
        'Canonical corporate entity matches official public records and domain headers.',
      verified_identifiers: [
        {
          type: 'SEC CIK',
          value: '0001652044',
          status: 'verified',
          source_url: 'https://www.sec.gov/edgar/browse/?CIK=0001652044',
        },
        {
          type: 'Delaware File Number',
          value: '3582691',
          status: 'verified',
          source_url: 'https://corp.delaware.gov/',
        },
        {
          type: 'Primary Domain',
          value: 'google.com',
          status: 'verified',
          source_url: 'https://google.com',
        },
      ],
    },
    registration_findings: {
      status: 'verified',
      summary:
        'Corporate registration active under Alphabet Inc. (Delaware Entity No. 3582691). Public SEC Form 10-K filings up to date.',
      findings: [
        {
          authority: 'Delaware Secretary of State',
          registration_number: '3582691',
          jurisdiction: 'Delaware, USA',
          status: 'verified',
          source_url: 'https://corp.delaware.gov/',
          date: '1998-09-04',
        },
        {
          authority: 'US Securities & Exchange Commission (SEC)',
          registration_number: 'CIK 0001652044',
          jurisdiction: 'United States',
          status: 'verified',
          source_url: 'https://www.sec.gov/edgar/browse/?CIK=0001652044',
          date: '2015-10-02',
        },
      ],
    },
    certification_findings: {
      status: 'verified',
      summary:
        'Holds ISO/IEC 27001, ISO/IEC 27017, ISO/IEC 27018, SOC 1/2/3, and FedRAMP High certifications.',
      certifications: [
        {
          name: 'ISO/IEC 27001:2022',
          issuer: 'EY CertifyPoint',
          validity: 'Active',
          status: 'verified',
          source_url: 'https://cloud.google.com/security/compliance/iso-27001',
        },
        {
          name: 'SOC 3 Security & Availability',
          issuer: 'PricewaterhouseCoopers LLP',
          validity: 'Active',
          status: 'verified',
          source_url: 'https://cloud.google.com/security/compliance/soc-3',
        },
        {
          name: 'FedRAMP High Authorization',
          issuer: 'FedRAMP PMO',
          validity: 'Active',
          status: 'verified',
          source_url: 'https://marketplace.fedramp.gov/products/FR1808453412',
        },
      ],
    },
    trust_score_explanation: {
      explanation:
        'Trust score 96/100 computed deterministically across 5 evidence dimensions. High domain authority, verified corporate filings, authenticated HTTPS endpoints, zero recruitment scam flags.',
      contributing_signals: [
        'Domain google.com active for >25 years',
        'Official careers portal hosted on subdomain (careers.google.com)',
        'Public SEC Form 10-K filings verified',
        'Valid DMARC/DKIM email authentication policies',
        'Verified ISO 27001 compliance documentation',
      ],
    },
    risk_score_explanation: {
      overall_risk: 'low',
      factors: [
        'No deceptive domain spoofing or lookalike typosquatting detected.',
        'Official job postings route exclusively through careers.google.com.',
        'No payment requests or wire transfer demands found in hiring workflows.',
      ],
    },
    recruitment_risk: {
      company_legitimacy: 'verified_authentic',
      job_offer_risk: 'low',
      careers_portal_verified: true,
      indicators: [
        'Hiring notices route exclusively through careers.google.com',
        'Email communications originate from @google.com domain',
        'Zero fee demands or security deposit requirements',
      ],
    },
    news_hiring: {
      summary:
        'Active global recruitment across software engineering, AI research, cloud operations, and product development.',
      active_hiring_channels: true,
      careers_url: 'https://careers.google.com',
      recent_events: [
        {
          title: 'Google Expands AI Research Infrastructure and Hiring in 2026',
          date: '2026-08-15',
          source: 'Google Official Blog',
          url: 'https://blog.google',
          summary:
            'Google announced ongoing investments in generative AI foundation models, expanding engineering presence across major global technology hubs.',
        },
        {
          title: 'Alphabet Reports Strong Cloud and AI Revenue Growth',
          date: '2026-07-28',
          source: 'Reuters Financial News',
          url: 'https://reuters.com',
          summary:
            'Alphabet Inc. quarterly financial earnings exceeded market expectations driven by Google Cloud and Gemini AI platform adoption.',
        },
      ],
    },
    hiring_intelligence: {
      careers_url: 'https://careers.google.com',
      status: 'active',
      open_roles_observed: true,
    },
    technology_reputation: {
      infrastructure:
        'Global Google Cloud Platform (GCP) network infrastructure, Borg cluster management, custom TPU v5e/v6 AI accelerators.',
      tech_stack: [
        'Python',
        'C++',
        'Go',
        'Java',
        'TensorFlow',
        'JAX',
        'Kubernetes',
        'Borg',
        'Spanner',
      ],
      engineering_presence:
        'Extensive open-source contributions, leading research publications in NeurIPS, ICML, ACL, and IEEE.',
      public_sentiment:
        'Overwhelmingly positive developer sentiment, high Glassdoor employer score (4.4/5.0).',
      signals: [
        {
          type: 'open_source',
          label: 'GitHub Organization google (2,500+ public repos)',
          confidence: 0.99,
          source_url: 'https://github.com/google',
        },
        {
          type: 'cloud_provider',
          label: 'Google Cloud Platform (cloud.google.com)',
          confidence: 1.0,
          source_url: 'https://cloud.google.com',
        },
      ],
    },
    reputation_intelligence: {
      public_sentiment: 'Positive / High Authority',
      employee_presence_verified: true,
      summary:
        'Verified workforce presence across 50+ countries with public LinkedIn corporate page confirming 180,000+ verified employees.',
    },
    trust_score: {
      score: 96,
      trust_index: 96,
      confidence: 0.98,
      risk_level: 'low',
      verification_status: 'verified',
      evidence_coverage: 1.0,
      algorithm_version: 'v1.0-multi-agent-m5',
      explanation:
        'Multi-agent forensic analysis confirmed corporate legitimacy, domain provenance, public SEC filings, and engineering presence.',
      calculated_at: new Date().toISOString(),
      dimension_scores: {
        identity_verification: {
          name: 'Identity Verification',
          score: 100,
          confidence: 1.0,
          weight: 0.25,
          weighted_score: 25.0,
          verification_status: 'verified',
          evidence_count: 6,
          evidence_ids: ['ev-1', 'ev-2'],
        },
        domain_provenance: {
          name: 'Domain Provenance',
          score: 98,
          confidence: 0.98,
          weight: 0.25,
          weighted_score: 24.5,
          verification_status: 'verified',
          evidence_count: 5,
          evidence_ids: ['ev-3', 'ev-4'],
        },
        registration_authenticity: {
          name: 'Registration Authenticity',
          score: 95,
          confidence: 0.95,
          weight: 0.20,
          weighted_score: 19.0,
          verification_status: 'verified',
          evidence_count: 4,
          evidence_ids: ['ev-5'],
        },
        recruitment_legitimacy: {
          name: 'Recruitment Legitimacy',
          score: 95,
          confidence: 0.95,
          weight: 0.15,
          weighted_score: 14.25,
          verification_status: 'verified',
          evidence_count: 5,
          evidence_ids: ['ev-6'],
        },
        reputation_engineering: {
          name: 'Reputation & Engineering',
          score: 92,
          confidence: 0.92,
          weight: 0.15,
          weighted_score: 13.8,
          verification_status: 'verified',
          evidence_count: 8,
          evidence_ids: ['ev-7', 'ev-8'],
        },
      },
    },
    references: [
      {
        index: 1,
        url: 'https://google.com',
        title: 'Google Official Website',
        sourceType: 'official_site',
        observedAt: new Date().toISOString(),
        reliability: 1.0,
      },
      {
        index: 2,
        url: 'https://careers.google.com',
        title: 'Google Careers Portal',
        sourceType: 'official_site',
        observedAt: new Date().toISOString(),
        reliability: 1.0,
      },
      {
        index: 3,
        url: 'https://www.sec.gov/edgar/browse/?CIK=0001652044',
        title: 'SEC EDGAR Public Filings — Alphabet Inc.',
        sourceType: 'government_registry',
        observedAt: new Date().toISOString(),
        reliability: 1.0,
      },
      {
        index: 4,
        url: 'https://cloud.google.com/security/compliance/iso-27001',
        title: 'Google Cloud Security Compliance — ISO 27001',
        sourceType: 'official_site',
        observedAt: new Date().toISOString(),
        reliability: 0.95,
      },
      {
        index: 5,
        url: 'https://github.com/google',
        title: 'Google Open Source GitHub Organization',
        sourceType: 'web_search',
        observedAt: new Date().toISOString(),
        reliability: 0.95,
      },
    ],
  },
};

export function getDemoReport(targetId?: string): Report {
  const reportId = targetId || 'demo-google-report-id';
  return {
    ...DEMO_GOOGLE_REPORT,
    id: reportId,
    research_run_id: reportId,
  };
}
