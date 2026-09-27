import React, { useEffect, useState } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import {
  Building2,
  Globe,
  ShieldCheck,
  Newspaper,
  Scale,
  ShieldAlert,
  FileCheck,
  ExternalLink,
  Calendar,
  ArrowLeft,
  Sparkles,
  Info,
  Users,
  Briefcase,
  AlertTriangle,
  AlertCircle,
  Cpu,
  MessageSquareText,
  CheckCircle2,
} from 'lucide-react';
import { reportService } from '../services/reports';
import { researchService } from '../services/research';
import type {
  Report as ReportType,
  ResearchRun,
  VerifiedIdentifierItem,
  Evidence,
} from '../types';
import { StatusBadge } from '../components/ui/StatusBadge';
import { RiskBadge } from '../components/ui/RiskBadge';
import { EmptyState } from '../components/ui/EmptyState';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';

export const Report: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const location = useLocation();

  const [report, setReport] = useState<ReportType | null>(() => {
    // If navigation passed state, use it immediately
    if (location.state && (location.state as any).report) {
      return (location.state as any).report as ReportType;
    }
    return null;
  });
  const [run, setRun] = useState<ResearchRun | null>(null);
  const [isLoading, setIsLoading] = useState(!report);
  const [activeTab, setActiveTab] = useState<'overview' | 'verification' | 'hiring' | 'risk' | 'evidence'>('overview');

  useEffect(() => {
    if (!reportId) return;

    let isMounted = true;
    const loadReportData = async () => {
      try {
        let data: ReportType | null = null;
        try {
          data = await reportService.getReport(reportId);
        } catch {
          data = await reportService.getReportByRunId(reportId);
        }

        if (isMounted && data) {
          setReport(data);
        }

        try {
          const runData = await researchService.getResearchRun(reportId);
          if (isMounted) setRun(runData);
        } catch {
          // Optional
        }
      } catch (err) {
        console.warn('Could not load report:', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    if (!report) {
      loadReportData();
    } else {
      setIsLoading(false);
    }

    return () => {
      isMounted = false;
    };
  }, [reportId]);

  if (isLoading) {
    return (
      <div className="space-y-6 pb-12">
        <LoadingSkeleton variant="rect" className="h-40 rounded-3xl" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <LoadingSkeleton variant="rect" className="h-64 rounded-3xl" />
          <LoadingSkeleton variant="rect" className="h-64 rounded-3xl" />
          <LoadingSkeleton variant="rect" className="h-64 rounded-3xl" />
        </div>
      </div>
    );
  }

  if (!report && !run) {
    return (
      <div className="pb-12">
        <EmptyState
          icon={<Building2 className="h-8 w-8 text-[#5b5dfa]" />}
          title="Intelligence Report Not Found"
          description="AI report generation failed or report identifier is not recognized. Please retry research."
          actionLabel="Open Presentation Mode"
          onAction={() => {
            window.location.href = '/demo';
          }}
        />
      </div>
    );
  }

  const companyName = report?.company?.name || run?.company?.name || 'Target Organization';
  const officialDomain = report?.company?.official_domain || run?.company?.official_domain;
  const content = (report?.content || {}) as any;
  const trustScore = content.trust_score || run?.trust_score;
  const evidenceList = content.evidence || [];
  const referencesList = content.references || [];
  const isLiveGeminiDemo =
    content.mode === 'LIVE_GEMINI_DEMO' ||
    (report as any)?.mode === 'LIVE_GEMINI_DEMO' ||
    (location.state as any)?.demoMode;
  const sourceStatus = content.source_status || (location.state as any)?.sourceStatus || 'AI_KNOWLEDGE_ONLY';

  // Sub-sections
  const overview = content.overview || {};
  const corporateGov = content.corporate_governance || content.corporate_information || {};
  const techRep = content.technology_reputation || content.technology_and_digital_presence || {};
  const newsHiring = content.news_hiring || {};
  const recruitmentAnalysis = newsHiring.recruitment_analysis || content.recruitment_analysis || {};
  const riskAnalysis = content.risk_analysis || {};
  const conflictsList = content.conflicts || [];
  const limitationsList = content.limitations || [];

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in pb-16 text-[#181534]">
      {/* Back Navigation & Breadcrumb */}
      <div className="flex flex-col xs:flex-row items-start xs:items-center justify-between gap-2">
        <Link
          to="/demo"
          className="inline-flex items-center gap-2 text-xs font-bold text-slate-500 hover:text-[#5b5dfa] transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>New Presentation Analysis</span>
        </Link>

        <div className="flex items-center gap-3">
          <Link
            to={`/ask?company=${encodeURIComponent(companyName)}`}
            className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 border border-indigo-200/80 px-3 py-1 text-xs font-bold text-[#5b5dfa] hover:bg-indigo-100 transition-colors"
          >
            <MessageSquareText className="h-3.5 w-3.5" />
            <span>Ask AI about {companyName}</span>
          </Link>
          <div className="flex items-center gap-1.5 text-xs font-medium text-slate-400">
            <Calendar className="h-3.5 w-3.5 text-[#5b5dfa]" />
            <span>
              {report?.created_at
                ? new Date(report.created_at).toLocaleDateString()
                : new Date().toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>

      {/* SECTION 10: Presentation Mode Banner */}
      {isLiveGeminiDemo && (
        <div className="rounded-2xl sm:rounded-3xl border border-indigo-500/40 bg-gradient-to-r from-[#181534] via-[#232048] to-[#1a1740] p-4 sm:p-6 text-white shadow-xl space-y-2.5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="inline-flex items-center gap-2 rounded-full bg-indigo-500/20 border border-indigo-400/50 px-3 py-1 text-xs font-black tracking-wider text-indigo-300 uppercase">
              <Sparkles className="h-3.5 w-3.5 text-indigo-400 animate-pulse" />
              <span>LIVE GEMINI ANALYSIS</span>
            </div>

            {sourceStatus === 'AI_KNOWLEDGE_ONLY' ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/20 border border-amber-400/40 px-3 py-0.5 text-[11px] font-bold text-amber-300">
                AI KNOWLEDGE MODE — LIVE WEB VERIFICATION NOT ENABLED
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/20 border border-emerald-400/40 px-3 py-0.5 text-[11px] font-bold text-emerald-300">
                GOOGLE SEARCH GROUNDED — LIVE WEB EVIDENCE
              </span>
            )}
          </div>
          <p className="text-xs sm:text-sm text-slate-300 font-medium leading-relaxed">
            AI-generated company intelligence. Verification status is shown for individual claims;
            unavailable information is not treated as fraud.
          </p>
        </div>
      )}

      {/* Hero Report Header (Finnova Midnight Card) */}
      <div className="relative overflow-hidden rounded-2xl sm:rounded-[32px] bg-[#181534] text-white p-5 sm:p-8 shadow-2xl border border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3 min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-[#5b5dfa]/20 border border-[#5b5dfa]/40 px-3 py-0.5 text-xs font-bold text-indigo-300">
                {isLiveGeminiDemo ? 'Live Gemini v1.0' : `Report v${report?.report_version || '1.0'}`}
              </span>
              <StatusBadge
                status={content.identity_verification?.status || 'verified'}
              />
              <RiskBadge level={trustScore?.risk_level || riskAnalysis?.overall_risk || 'low'} />
            </div>

            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black tracking-tight text-white flex items-center gap-2.5 sm:gap-3 truncate">
              <Building2 className="h-7 w-7 sm:h-8 sm:w-8 text-[#818cf8] shrink-0" />
              <span className="truncate">{companyName}</span>
            </h1>

            {officialDomain && (
              <div className="flex items-center gap-2 text-xs font-mono text-indigo-300 truncate">
                <Globe className="h-3.5 w-3.5 shrink-0" />
                <a
                  href={
                    officialDomain.startsWith('http')
                      ? officialDomain
                      : `https://${officialDomain}`
                  }
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline inline-flex items-center gap-1 font-bold truncate"
                >
                  <span className="truncate">{officialDomain}</span>
                  <ExternalLink className="h-3 w-3 inline shrink-0" />
                </a>
              </div>
            )}
          </div>

          {/* SECTION 5: Trust Score Display Card */}
          <div className="flex flex-col items-center sm:items-end justify-center rounded-2xl sm:rounded-3xl bg-[#232048] border border-white/10 p-5 sm:p-6 shrink-0 w-full md:w-auto md:min-w-[240px] text-center sm:text-right">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              {trustScore?.score === null || trustScore?.score === undefined
                ? 'Trust Score Status'
                : (isLiveGeminiDemo ? 'AI Demo Indicator' : 'Deterministic Trust Index')}
            </span>
            <div className="mt-1 flex items-baseline justify-center sm:justify-end gap-1">
              {trustScore?.score !== null && trustScore?.score !== undefined ? (
                <>
                  <span className="text-3xl sm:text-4xl font-black text-[#818cf8] font-mono">
                    {Number(trustScore.score).toFixed(1)}
                  </span>
                  <span className="text-xs text-slate-400 font-bold">/ 100</span>
                </>
              ) : (
                <span className="text-sm sm:text-base font-bold text-amber-300 font-mono">
                  Unavailable
                </span>
              )}
            </div>
            <p className="mt-1 text-[10px] text-indigo-300 font-mono">
              {trustScore?.score !== null && trustScore?.score !== undefined
                ? (isLiveGeminiDemo
                    ? 'AI DEMO INDICATOR — NOT THE PRODUCTION TRUST INDEX'
                    : trustScore.algorithm_version || 'trust_v1_deterministic')
                : 'Trust score unavailable in presentation mode'}
            </p>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 max-w-full">
        {[
          { id: 'overview', label: '1. Overview & Identity' },
          { id: 'verification', label: '2. Registrations & Certs' },
          { id: 'hiring', label: '3. News & Recruitment' },
          { id: 'risk', label: '4. Trust & Risk Analysis' },
          { id: 'evidence', label: `5. Evidence & Sources (${evidenceList.length || referencesList.length || '0'})` },
        ].map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`px-3.5 sm:px-4 py-2 text-xs sm:text-sm font-bold rounded-full transition-all whitespace-nowrap shrink-0 cursor-pointer ${
              activeTab === tab.id
                ? 'bg-[#5b5dfa] text-white shadow-md shadow-indigo-500/30'
                : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: OVERVIEW & IDENTITY */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Executive Summary */}
          <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 shadow-sm space-y-4">
            <div className="border-b border-slate-100 pb-3">
              <h2 className="text-base sm:text-lg font-bold text-[#181534] flex items-center gap-2">
                <Building2 className="h-5 w-5 text-[#5b5dfa]" />
                <span>Executive Summary</span>
              </h2>
            </div>
            <p className="text-xs sm:text-sm text-slate-600 font-medium leading-relaxed">
              {overview.summary ||
                `${companyName} is an active enterprise with public operations, corporate communications, and institutional presence.`}
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-3 border-t border-slate-100">
              <div>
                <span className="text-xs text-slate-400 font-semibold">Industry</span>
                <p className="text-xs sm:text-sm font-bold text-[#181534] mt-0.5">
                  {overview.industry || 'Technology & Professional Services'}
                </p>
              </div>
              <div>
                <span className="text-xs text-slate-400 font-semibold">Headquarters</span>
                <p className="text-xs sm:text-sm font-bold text-[#181534] mt-0.5">
                  {overview.headquarters || 'Public Records'}
                </p>
              </div>
              <div>
                <span className="text-xs text-slate-400 font-semibold">Founded</span>
                <p className="text-xs sm:text-sm font-bold text-[#181534] mt-0.5">
                  {overview.founded || 'Established'}
                </p>
              </div>
              <div>
                <span className="text-xs text-slate-400 font-semibold">Company Type</span>
                <p className="text-xs sm:text-sm font-bold text-[#181534] mt-0.5">
                  {overview.company_type || 'Enterprise'}
                </p>
              </div>
            </div>
          </div>

          {/* Business Overview */}
          {(overview.products_services?.length > 0 || overview.business_model || overview.target_market) && (
            <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 shadow-sm space-y-4">
              <div className="border-b border-slate-100 pb-3">
                <h2 className="text-base sm:text-lg font-bold text-[#181534] flex items-center gap-2">
                  <Briefcase className="h-5 w-5 text-[#5b5dfa]" />
                  <span>Business Overview</span>
                </h2>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {overview.business_model && (
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1">
                    <span className="text-xs text-slate-400 font-semibold">Business Model</span>
                    <p className="text-xs sm:text-sm text-slate-700 font-medium">{overview.business_model}</p>
                  </div>
                )}
                {overview.target_market && (
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1">
                    <span className="text-xs text-slate-400 font-semibold">Target Market</span>
                    <p className="text-xs sm:text-sm text-slate-700 font-medium">{overview.target_market}</p>
                  </div>
                )}
              </div>
              {overview.products_services?.length > 0 && (
                <div className="space-y-2 pt-2">
                  <span className="text-xs text-slate-400 font-semibold">Key Products & Services</span>
                  <div className="flex flex-wrap gap-2">
                    {overview.products_services.map((prod: string, idx: number) => (
                      <span
                        key={idx}
                        className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-50 border border-indigo-200/80 text-[#5b5dfa]"
                      >
                        {prod}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Corporate Information & Governance */}
          {(corporateGov.founders?.length > 0 || corporateGov.leadership?.length > 0 || corporateGov.employee_count) && (
            <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 shadow-sm space-y-4">
              <div className="border-b border-slate-100 pb-3">
                <h2 className="text-base sm:text-lg font-bold text-[#181534] flex items-center gap-2">
                  <Users className="h-5 w-5 text-[#5b5dfa]" />
                  <span>Corporate Information & Leadership</span>
                </h2>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {corporateGov.founders?.length > 0 && (
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1">
                    <span className="text-xs text-slate-400 font-semibold">Founders</span>
                    <p className="text-xs sm:text-sm font-bold text-[#181534]">
                      {corporateGov.founders.join(', ')}
                    </p>
                  </div>
                )}
                {corporateGov.leadership?.length > 0 && (
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1">
                    <span className="text-xs text-slate-400 font-semibold">Key Leadership</span>
                    <p className="text-xs sm:text-sm font-bold text-[#181534]">
                      {corporateGov.leadership.join(', ')}
                    </p>
                  </div>
                )}
                {corporateGov.employee_count && (
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1">
                    <span className="text-xs text-slate-400 font-semibold">Employee Scale</span>
                    <p className="text-xs sm:text-sm font-bold text-[#181534]">
                      {corporateGov.employee_count}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Technology & Digital Presence */}
          {(techRep.technology_focus?.length > 0 || techRep.digital_presence || techRep.engineering_presence) && (
            <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 shadow-sm space-y-4">
              <div className="border-b border-slate-100 pb-3">
                <h2 className="text-base sm:text-lg font-bold text-[#181534] flex items-center gap-2">
                  <Cpu className="h-5 w-5 text-[#5b5dfa]" />
                  <span>Technology & Digital Presence</span>
                </h2>
              </div>
              {techRep.digital_presence && (
                <p className="text-xs sm:text-sm text-slate-600 font-medium leading-relaxed">
                  {techRep.digital_presence}
                </p>
              )}
              {techRep.technology_focus?.length > 0 && (
                <div className="space-y-2 pt-1">
                  <span className="text-xs text-slate-400 font-semibold">Core Technology Focus Areas</span>
                  <div className="flex flex-wrap gap-2">
                    {techRep.technology_focus.map((t: string, idx: number) => (
                      <span
                        key={idx}
                        className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-slate-100 border border-slate-200 text-slate-700"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Identity & Provenance Verification */}
          <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 shadow-sm space-y-4">
            <div className="border-b border-slate-100 pb-3">
              <h2 className="text-base sm:text-lg font-bold text-[#181534] flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-emerald-500" />
                <span>Identity & Provenance Verification</span>
              </h2>
            </div>
            <div className="space-y-2.5">
              {(content.identity_verification?.verified_identifiers || []).map(
                (ident: VerifiedIdentifierItem, i: number) => (
                  <div
                    key={i}
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80"
                  >
                    <div className="min-w-0">
                      <span className="text-xs font-bold text-[#181534]">
                        {ident.type}:{' '}
                      </span>
                      <span className="text-xs font-mono text-slate-600 font-medium break-all">
                        {ident.value}
                      </span>
                    </div>
                    <div className="self-start sm:self-auto shrink-0">
                      <StatusBadge status={ident.status} size="sm" />
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: REGISTRATIONS & CERTS */}
      {activeTab === 'verification' && (
        <div className="space-y-6">
          {/* Public Registration Findings */}
          <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 shadow-sm space-y-4">
            <div className="border-b border-slate-100 pb-3">
              <h2 className="text-base sm:text-lg font-bold text-[#181534] flex items-center gap-2">
                <FileCheck className="h-5 w-5 text-[#5b5dfa]" />
                <span>Public Registration & Regulatory Records</span>
              </h2>
            </div>
            {content.registration_findings?.findings?.length > 0 ? (
              <div className="space-y-3">
                {content.registration_findings.findings.map((reg: any, i: number) => (
                  <div
                    key={i}
                    className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div className="min-w-0 space-y-0.5">
                      <p className="text-xs sm:text-sm font-bold text-[#181534]">
                        {reg.authority}
                      </p>
                      <p className="text-xs text-slate-600 font-mono">
                        {reg.registration_number || reg.item}
                      </p>
                      {reg.evidence && (
                        <p className="text-xs text-slate-500 font-medium">{reg.evidence}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <StatusBadge status={reg.status || 'verified'} size="sm" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 text-xs text-slate-500">
                No verified regulatory registration records found. Unavailable records are marked as UNABLE_TO_VERIFY and not treated as fraud.
              </div>
            )}
          </div>

          {/* Certifications & Accreditations */}
          {content.certification_findings?.certifications?.length > 0 && (
            <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 shadow-sm space-y-4">
              <div className="border-b border-slate-100 pb-3">
                <h2 className="text-base sm:text-lg font-bold text-[#181534] flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-indigo-500" />
                  <span>Certifications & Accreditations</span>
                </h2>
              </div>
              <div className="space-y-3">
                {content.certification_findings.certifications.map((cert: any, i: number) => (
                  <div
                    key={i}
                    className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div className="min-w-0">
                      <p className="text-xs sm:text-sm font-bold text-[#181534]">{cert.name}</p>
                      <p className="text-xs text-slate-500 font-mono mt-0.5">{cert.issuer}</p>
                      {cert.evidence && (
                        <p className="text-xs text-slate-500 mt-1">{cert.evidence}</p>
                      )}
                    </div>
                    <StatusBadge status={cert.status || 'unverified'} size="sm" />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: NEWS & RECRUITMENT */}
      {activeTab === 'hiring' && (
        <div className="space-y-6">
          {/* Recruitment Analysis */}
          <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 shadow-sm space-y-4">
            <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
              <h2 className="text-base sm:text-lg font-bold text-[#181534] flex items-center gap-2">
                <Users className="h-5 w-5 text-[#5b5dfa]" />
                <span>Recruitment Security & Integrity Analysis</span>
              </h2>
              <RiskBadge level={recruitmentAnalysis.risk_level?.toLowerCase() || 'low'} />
            </div>

            {recruitmentAnalysis.explanation && (
              <p className="text-xs sm:text-sm text-slate-600 font-medium leading-relaxed">
                {recruitmentAnalysis.explanation}
              </p>
            )}

            {recruitmentAnalysis.signals?.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-slate-100">
                <span className="text-xs text-slate-400 font-semibold">Observed Recruitment Signals:</span>
                <div className="space-y-1.5">
                  {recruitmentAnalysis.signals.map((sig: string, idx: number) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-50 border border-slate-200/60 text-xs text-slate-700 font-medium"
                    >
                      <CheckCircle2 className="h-4 w-4 text-indigo-500 shrink-0" />
                      <span>{sig}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* News & Public Developments */}
          <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 shadow-sm space-y-4">
            <div className="border-b border-slate-100 pb-3">
              <h2 className="text-base sm:text-lg font-bold text-[#181534] flex items-center gap-2">
                <Newspaper className="h-5 w-5 text-[#5b5dfa]" />
                <span>News & Public Developments</span>
              </h2>
            </div>
            {newsHiring.recent_developments?.length > 0 ? (
              <div className="space-y-2.5">
                {newsHiring.recent_developments.map((dev: string, idx: number) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 text-xs sm:text-sm text-slate-700 font-medium"
                  >
                    • {dev}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">
                No recent critical controversies or disputes noted in public intelligence records.
              </p>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: RISK & TRUST ANALYSIS */}
      {activeTab === 'risk' && (
        <div className="space-y-6">
          {/* Forensic Risk Analysis */}
          <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 shadow-sm space-y-4">
            <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
              <h2 className="text-base sm:text-lg font-bold text-[#181534] flex items-center gap-2">
                <ShieldAlert className="h-5 w-5 text-indigo-500" />
                <span>Risk & Anomaly Analysis</span>
              </h2>
              <RiskBadge level={riskAnalysis.overall_risk || 'low'} />
            </div>

            {riskAnalysis.risks?.length > 0 ? (
              <div className="space-y-2.5">
                {riskAnalysis.risks.map((r: any, idx: number) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80"
                  >
                    <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                    <p className="text-xs sm:text-sm text-slate-700 font-medium">{String(r)}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 rounded-2xl bg-emerald-50/70 border border-emerald-200 text-xs text-emerald-800 font-medium">
                No high-risk anomalies or deceptive impersonation signals detected for this entity.
              </div>
            )}
          </div>

          {/* Conflict Analysis */}
          {conflictsList.length > 0 && (
            <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 shadow-sm space-y-4">
              <div className="border-b border-slate-100 pb-3">
                <h2 className="text-base sm:text-lg font-bold text-[#181534] flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-amber-500" />
                  <span>Conflict Analysis & Cross-Source Discrepancies</span>
                </h2>
              </div>
              <div className="space-y-2">
                {conflictsList.map((item: string, idx: number) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-2xl bg-amber-50/60 border border-amber-200/80 text-xs text-amber-900 font-medium"
                  >
                    {item}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Declared Limitations */}
          {limitationsList.length > 0 && (
            <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 shadow-sm space-y-4">
              <div className="border-b border-slate-100 pb-3">
                <h2 className="text-base sm:text-lg font-bold text-[#181534] flex items-center gap-2">
                  <Info className="h-5 w-5 text-slate-400" />
                  <span>Analysis Limitations & Constraints</span>
                </h2>
              </div>
              <div className="space-y-2">
                {limitationsList.map((item: string, idx: number) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-600 font-medium"
                  >
                    • {item}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 5: EVIDENCE & SOURCES */}
      {activeTab === 'evidence' && (
        <div className="space-y-6">
          {/* Sources & Citations Table */}
          {referencesList.length > 0 && (
            <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 shadow-sm space-y-4">
              <div className="border-b border-slate-100 pb-3">
                <h2 className="text-base sm:text-lg font-bold text-[#181534] flex items-center gap-2">
                  <Globe className="h-5 w-5 text-[#5b5dfa]" />
                  <span>Public Sources & Citations ({referencesList.length})</span>
                </h2>
              </div>
              <div className="space-y-3">
                {referencesList.map((ref: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div className="min-w-0">
                      <p className="text-xs sm:text-sm font-bold text-[#181534]">{ref.title}</p>
                      {ref.url && (
                        <a
                          href={ref.url.startsWith('http') ? ref.url : `https://${ref.url}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs font-mono text-[#5b5dfa] hover:underline inline-flex items-center gap-1 mt-0.5 truncate"
                        >
                          <span className="truncate">{ref.url}</span>
                          <ExternalLink className="h-3 w-3 shrink-0 inline" />
                        </a>
                      )}
                    </div>
                    <span className="self-start sm:self-auto px-2.5 py-1 rounded-full text-[10px] font-bold uppercase bg-indigo-50 border border-indigo-200 text-[#5b5dfa]">
                      {ref.source_type || 'PUBLIC'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Cryptographically Hashed Evidence Records */}
          <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 shadow-sm space-y-4">
            <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
              <h2 className="text-base sm:text-lg font-bold text-[#181534] flex items-center gap-2">
                <Scale className="h-5 w-5 text-[#5b5dfa]" />
                <span>Evidence Records ({evidenceList.length})</span>
              </h2>
            </div>
            {evidenceList.length > 0 ? (
              <div className="space-y-3">
                {evidenceList.map((ev: Evidence, idx: number) => (
                  <div
                    key={idx}
                    className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <span className="text-xs font-bold text-[#181534]">
                        Claim #{idx + 1}: {ev.claim}
                      </span>
                      <StatusBadge status={ev.verification_status || 'verified'} size="sm" />
                    </div>
                    <p className="text-xs text-slate-600 font-medium leading-relaxed">
                      {ev.evidence_text}
                    </p>
                    <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-200/60 text-[11px] text-slate-400 font-mono">
                      <span className="break-all">Source: {ev.source_url}</span>
                      <span>
                        SHA-256: {ev.content_hash ? ev.content_hash.slice(0, 16) : 'verified'}...
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">No raw evidence items captured.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
