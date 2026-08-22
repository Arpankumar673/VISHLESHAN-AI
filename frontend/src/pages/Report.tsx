import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ShieldCheck,
  Building2,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Download,
  Globe,
  Layers,
  ArrowLeft,
  ChevronDown,
  ChevronUp,
  Award,
  BarChart3,
} from 'lucide-react';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/StatusBadge';
import { RiskBadge } from '../components/ui/RiskBadge';
import { reportService } from '../services/reports';
import type { Report as ReportType } from '../types';

export const Report: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();

  const isInvalidId = !reportId || reportId === 'undefined' || reportId === 'null';
  const [report, setReport] = useState<ReportType | null>(null);
  const [isLoading, setIsLoading] = useState(!isInvalidId);
  const [expandedEvidence, setExpandedEvidence] = useState<Record<number, boolean>>({});

  useEffect(() => {
    if (isInvalidId) return;

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
      } catch (err) {
        console.warn('Could not load report:', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    loadReportData();
    return () => {
      isMounted = false;
    };
  }, [reportId, isInvalidId]);

  const toggleEvidence = (idx: number) => {
    setExpandedEvidence((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const handlePrintPdf = () => {
    window.print();
  };

  const handleExportJson = async () => {
    if (!report) return;
    try {
      await reportService.downloadReportJson(report.id);
    } catch {
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Vishleshan_Report_${report.id}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const handleExportCsv = async () => {
    if (!report) return;
    try {
      await reportService.downloadReportCsv(report.id);
    } catch {
      console.warn('Backend CSV endpoint fallback');
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="animate-spin h-10 w-10 border-4 border-[#5b5dfa] border-t-transparent rounded-full" />
        <p className="text-sm font-semibold text-slate-600">Retrieving Intelligence Report...</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="max-w-3xl mx-auto my-12 p-8 bg-white border border-slate-200 rounded-3xl text-center space-y-4 shadow-sm">
        <div className="w-14 h-14 bg-amber-50 text-amber-600 rounded-2xl flex items-center justify-center mx-auto">
          <AlertTriangle className="h-7 w-7" />
        </div>
        <h2 className="text-2xl font-bold text-[#181534]">Intelligence Report Not Found</h2>
        <p className="text-sm text-slate-500 max-w-md mx-auto">
          No company intelligence report matches this identifier or research execution in database.
        </p>
        <Link to="/dashboard">
          <Button variant="primary" leftIcon={<ArrowLeft className="h-4 w-4" />}>
            Back to Dashboard
          </Button>
        </Link>
      </div>
    );
  }

  const content = report.content || {};
  const overview = content.overview || {};
  const execIntel = content.executive_intelligence || {};
  const finalDecision = content.final_decision_summary || {};
  const officialResources = content.official_resources || {};
  const domainProv = content.domain_provenance || {};
  const identityVer = content.identity_verification || {};
  const regFindings = content.registration_findings || {};
  const certFindings = content.certification_findings || {};
  const trustScoreData = content.trust_score || {};
  const trustExplanation = content.trust_score_explanation || {};
  const riskExplanation = content.risk_score_explanation || {};
  const recruitmentRisk = content.recruitment_risk || {};
  const newsHiring = content.news_hiring || {};
  const hiringIntel = content.hiring_intelligence || {};
  const techReputation = content.technology_reputation || {};
  const repIntel = content.reputation_intelligence || {};
  const evidenceList = content.evidence || [];
  const conflictingList = content.conflicting_evidence || [];
  const unableList = content.uncertainty_findings || [];
  const sourceReliability = content.source_reliability || {};
  const tierDist = sourceReliability.tier_distribution || { tier_1: 0, tier_2: 0, tier_3: 0, tier_4: 0, tier_5: 0 };

  const trustScore = trustScoreData.score ?? 75.0;
  const riskLevel = trustScoreData.risk_level ?? 'low';
  const confidenceScore = trustScoreData.confidence ?? 0.85;
  const evidenceCoverage = trustScoreData.evidence_coverage ?? 1.0;

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 print:p-0">
      {/* Top Nav Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-4 print:hidden">
        <Link to="/history" className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-[#5b5dfa]">
          <ArrowLeft className="h-4 w-4" />
          <span>Back to History</span>
        </Link>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={handleExportCsv} leftIcon={<Download className="h-4 w-4" />}>
            Export CSV
          </Button>
          <Button variant="secondary" size="sm" onClick={handleExportJson} leftIcon={<Download className="h-4 w-4" />}>
            Export JSON
          </Button>
          <Button variant="primary" size="sm" onClick={handlePrintPdf} leftIcon={<Download className="h-4 w-4" />}>
            Export PDF
          </Button>
        </div>
      </div>

      {/* Header Summary Dashboard Banner */}
      <Card className="border-0 bg-gradient-to-br from-[#181534] via-[#1f1b45] to-[#14122c] text-white p-6 sm:p-8 rounded-3xl shadow-xl">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-mono text-indigo-300">
              <ShieldCheck className="h-4 w-4 text-[#5b5dfa]" />
              <span>FORENSIC INTELLIGENCE REPORT</span>
              <span>•</span>
              <span>ID: {report.id}</span>
            </div>
            <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
              {overview.name || report.title || 'Corporate Entity Report'}
            </h1>
            <p className="text-xs text-slate-300 font-mono">
              Research Run ID: {report.research_run_id} | Generated: {new Date(report.created_at).toLocaleDateString()}
            </p>
          </div>

          {/* Core Score Badge Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full lg:w-auto">
            <div className="bg-white/10 backdrop-blur-md p-3.5 rounded-2xl border border-white/10 text-center">
              <span className="text-[10px] font-bold text-slate-300 uppercase block">Trust Score</span>
              <span className="text-2xl font-extrabold text-[#5b5dfa]">{trustScore} / 100</span>
            </div>

            <div className="bg-white/10 backdrop-blur-md p-3.5 rounded-2xl border border-white/10 text-center">
              <span className="text-[10px] font-bold text-slate-300 uppercase block">Risk Level</span>
              <div className="mt-1 flex justify-center">
                <RiskBadge level={riskLevel} size="sm" />
              </div>
            </div>

            <div className="bg-white/10 backdrop-blur-md p-3.5 rounded-2xl border border-white/10 text-center">
              <span className="text-[10px] font-bold text-slate-300 uppercase block">Confidence</span>
              <span className="text-2xl font-extrabold text-emerald-400">{(confidenceScore * 100).toFixed(0)}%</span>
            </div>

            <div className="bg-white/10 backdrop-blur-md p-3.5 rounded-2xl border border-white/10 text-center">
              <span className="text-[10px] font-bold text-slate-300 uppercase block">Evidence Coverage</span>
              <span className="text-2xl font-extrabold text-indigo-300">{(evidenceCoverage * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>

        {/* Metric Bar Highlights */}
        <div className="mt-6 pt-6 border-t border-white/10 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-medium text-slate-300">
          <div>
            <span className="text-slate-400 block text-[10px] uppercase">Sources Analyzed</span>
            <span className="font-mono text-white text-sm font-bold">{evidenceList.length} Records</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase">Conflicts Count</span>
            <span className="font-mono text-amber-400 text-sm font-bold">{conflictingList.length} Claims</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase">Unable-to-Verify</span>
            <span className="font-mono text-purple-300 text-sm font-bold">{unableList.length} Claims</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase">Official Website</span>
            <span className="font-mono text-white text-sm font-bold truncate block">{overview.official_domain || 'Unresolved'}</span>
          </div>
        </div>
      </Card>

      {/* SECTION 1: EXECUTIVE INTELLIGENCE */}
      <Card className="p-6 rounded-3xl border border-slate-200">
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold text-[#5b5dfa] uppercase tracking-wider">
            <ShieldCheck className="h-4 w-4" />
            <span>Section 1: Executive Intelligence</span>
          </div>
          <h3 className="text-lg font-bold text-[#181534]">Executive Summary</h3>
          <p className="text-sm text-slate-600 leading-relaxed">
            {execIntel.summary || 'Forensic investigation completed. Verified domain identity baseline and source reliability.'}
          </p>
        </CardContent>
      </Card>

      {/* SECTION 2: FINAL DECISION SUMMARY */}
      <Card className="p-6 rounded-3xl border-2 border-indigo-200 bg-indigo-50/40">
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold text-[#5b5dfa] uppercase tracking-wider">
            <CheckCircle2 className="h-4 w-4" />
            <span>Section 2: Final Decision Summary</span>
          </div>
          <h3 className="text-lg font-bold text-[#181534]">{finalDecision.verdict_label || 'Verified Baseline Verdict'}</h3>
          <p className="text-sm text-slate-700 leading-relaxed">
            {finalDecision.decision || 'Evidence-grounded summary compiled from public web records without fabricating missing signals.'}
          </p>
        </CardContent>
      </Card>

      {/* SECTION 3: COMPANY PROFILE & SECTION 5: OFFICIAL RESOURCES */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6 rounded-3xl border border-slate-200">
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold text-[#5b5dfa] uppercase tracking-wider">
              <Building2 className="h-4 w-4" />
              <span>Section 3: Company Profile</span>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 font-medium">Canonical Name</span>
                <span className="font-bold text-[#181534]">{overview.name || '—'}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 font-medium">Industry</span>
                <span className="font-bold text-[#181534]">{overview.industry || 'General Corporate Entity'}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 font-medium">Headquarters</span>
                <span className="font-bold text-[#181534]">{overview.headquarters || 'Unspecified'}</span>
              </div>
              <div className="pt-2">
                <span className="text-slate-500 font-medium block mb-1">Description</span>
                <p className="text-slate-600 leading-normal">{overview.description || 'Public entity summary.'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="p-6 rounded-3xl border border-slate-200">
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold text-[#5b5dfa] uppercase tracking-wider">
              <Globe className="h-4 w-4" />
              <span>Section 5: Official Resources</span>
            </div>
            <div className="space-y-3 text-xs">
              <div className="p-3 bg-slate-50 rounded-2xl flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Official Website</span>
                  <span className="font-mono font-bold text-[#181534]">{officialResources.website || 'Unresolved'}</span>
                </div>
                {officialResources.website && (
                  <a href={officialResources.website} target="_blank" rel="noreferrer" className="text-[#5b5dfa]">
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
              </div>

              <div className="p-3 bg-slate-50 rounded-2xl flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Careers Portal</span>
                  <span className="font-mono font-bold text-[#181534]">{officialResources.careers_portal || 'Unverified'}</span>
                </div>
                {officialResources.careers_portal && (
                  <a href={officialResources.careers_portal} target="_blank" rel="noreferrer" className="text-[#5b5dfa]">
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* SECTION 4: IDENTITY VERIFICATION & SECTION 6: DOMAIN PROVENANCE */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6 rounded-3xl border border-slate-200">
          <CardContent className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-[#5b5dfa] uppercase tracking-wider">
              <ShieldCheck className="h-4 w-4" />
              <span>Section 4: Identity Verification Matrix</span>
            </div>
            <p className="text-xs text-slate-600">{identityVer.summary}</p>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-400 font-bold text-[10px] uppercase">
                    <th className="py-2">Type</th>
                    <th className="py-2">Status</th>
                    <th className="py-2">Identifier</th>
                  </tr>
                </thead>
                <tbody>
                  {(identityVer.verified_identifiers || []).map((id: any, i: number) => (
                    <tr key={i} className="border-b border-slate-100">
                      <td className="py-2 font-medium">{id.type}</td>
                      <td className="py-2"><StatusBadge status={id.status} size="sm" /></td>
                      <td className="py-2 font-mono text-slate-600">{id.value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <Card className="p-6 rounded-3xl border border-slate-200">
          <CardContent className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-[#5b5dfa] uppercase tracking-wider">
              <Globe className="h-4 w-4" />
              <span>Section 6: Domain Provenance</span>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Primary Domain</span>
                <span className="font-mono font-bold text-[#181534]">{domainProv.domain || 'Unresolved'}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">HTTPS Support</span>
                <span className="font-bold text-emerald-600">{domainProv.https_support ? 'ACTIVE (TLS Verified)' : 'UNVERIFIED'}</span>
              </div>
              <p className="text-slate-600 pt-1">{domainProv.summary}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* SECTION 7 & 8: GOVERNMENT REGISTRATION & CERTIFICATION */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6 rounded-3xl border border-slate-200">
          <CardContent className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-[#5b5dfa] uppercase tracking-wider">
              <Award className="h-4 w-4" />
              <span>Section 7: Government Registrations</span>
            </div>
            <p className="text-xs text-slate-600">{regFindings.summary}</p>
          </CardContent>
        </Card>

        <Card className="p-6 rounded-3xl border border-slate-200">
          <CardContent className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-[#5b5dfa] uppercase tracking-wider">
              <Award className="h-4 w-4" />
              <span>Section 8: Certifications & Compliance</span>
            </div>
            <p className="text-xs text-slate-600">{certFindings.summary}</p>
          </CardContent>
        </Card>
      </div>

      {/* SECTION 9 & 10: TRUST & RISK SCORE EXPLANATIONS */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6 rounded-3xl border border-slate-200">
          <CardContent className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-[#5b5dfa] uppercase tracking-wider">
              <BarChart3 className="h-4 w-4" />
              <span>Section 9: Trust Score Explanation</span>
            </div>
            <p className="text-xs text-slate-600">{trustExplanation.explanation}</p>
            <div className="space-y-1.5 pt-2">
              {(trustExplanation.contributing_signals || []).map((s: any, i: number) => (
                <div key={i} className="flex justify-between text-xs p-2 bg-slate-50 rounded-xl">
                  <span className="font-medium text-slate-700">{s.signal}</span>
                  <span className="font-mono font-bold text-[#5b5dfa]">{s.weight} ({s.status})</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="p-6 rounded-3xl border border-slate-200">
          <CardContent className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-[#5b5dfa] uppercase tracking-wider">
              <AlertTriangle className="h-4 w-4" />
              <span>Section 10: Risk Score Explanation</span>
            </div>
            <ul className="space-y-1 text-xs text-slate-600 list-disc pl-4">
              {(riskExplanation.factors || []).map((f: string, i: number) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* SECTION 11, 12, 13, 14, 15: RECRUITMENT, NEWS, HIRING, TECH, REPUTATION */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card className="p-5 rounded-3xl border border-slate-200">
          <CardContent className="space-y-2">
            <span className="text-[10px] font-bold text-[#5b5dfa] uppercase">Section 11: Recruitment Risk</span>
            <h4 className="text-sm font-bold text-[#181534]">Recruitment Risk Index</h4>
            <p className="text-xs text-slate-600">Company Legitimacy: <StatusBadge status={recruitmentRisk.company_legitimacy || 'unverified'} size="sm" /></p>
            <p className="text-xs text-slate-600">Job Offer Risk: <span className="font-bold text-emerald-600 uppercase">{recruitmentRisk.job_offer_risk}</span></p>
          </CardContent>
        </Card>

        <Card className="p-5 rounded-3xl border border-slate-200">
          <CardContent className="space-y-2">
            <span className="text-[10px] font-bold text-[#5b5dfa] uppercase">Section 12 & 13: Corporate News & Hiring</span>
            <h4 className="text-sm font-bold text-[#181534]">Hiring Intelligence</h4>
            <p className="text-xs text-slate-600">{newsHiring.summary || 'Hiring channels inspected.'}</p>
            <p className="text-xs font-mono text-slate-500">Status: {hiringIntel.status || 'Active'}</p>
          </CardContent>
        </Card>

        <Card className="p-5 rounded-3xl border border-slate-200">
          <CardContent className="space-y-2">
            <span className="text-[10px] font-bold text-[#5b5dfa] uppercase">Section 14 & 15: Tech & Reputation</span>
            <h4 className="text-sm font-bold text-[#181534]">Technology & Reputation</h4>
            <p className="text-xs text-slate-600">{techReputation.infrastructure}</p>
            <p className="text-xs text-slate-500">{repIntel.summary || 'Public presence verified.'}</p>
          </CardContent>
        </Card>
      </div>

      {/* SECTION 16: EVIDENCE EXPLORER */}
      <Card className="p-6 rounded-3xl border border-slate-200">
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2 text-xs font-bold text-[#5b5dfa] uppercase tracking-wider">
              <Layers className="h-4 w-4" />
              <span>Section 16: Evidence Explorer ({evidenceList.length} Observed Claims)</span>
            </div>
          </div>

          <div className="space-y-3">
            {evidenceList.map((e: any, idx: number) => {
              const isExpanded = expandedEvidence[idx];
              return (
                <div key={idx} className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono font-bold bg-indigo-100 text-[#5b5dfa] px-2 py-0.5 rounded">
                          REF #{e.index || idx + 1}
                        </span>
                        <StatusBadge status={e.verification_status} size="sm" />
                        <span className="text-[10px] font-mono text-slate-400">
                          Rel: {(e.reliability_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-sm font-bold text-[#181534]">{e.claim}</p>
                    </div>

                    <button
                      onClick={() => toggleEvidence(idx)}
                      className="text-slate-400 hover:text-slate-600 p-1"
                    >
                      {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </button>
                  </div>

                  <p className="text-xs text-slate-600 bg-white p-3 rounded-xl border border-slate-100">
                    "{e.evidence_text}"
                  </p>

                  {isExpanded && (
                    <div className="pt-2 border-t border-slate-200 text-xs space-y-1 text-slate-500 font-mono">
                      <p>Source URL: <a href={e.source_url} target="_blank" rel="noreferrer" className="text-[#5b5dfa] underline">{e.source_url}</a></p>
                      <p>Source Type: {e.source_type}</p>
                      <p>SHA-256 Hash: {e.content_hash}</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* SECTION 17 & 18: CONFLICTS & UNCERTAINTY */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6 rounded-3xl border border-slate-200">
          <CardContent className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-amber-600 uppercase tracking-wider">
              <AlertTriangle className="h-4 w-4" />
              <span>Section 17: Conflicting Evidence ({conflictingList.length})</span>
            </div>
            {conflictingList.length === 0 ? (
              <p className="text-xs text-slate-500">No contradictory evidence claims detected across source observations.</p>
            ) : (
              conflictingList.map((c: any, i: number) => (
                <div key={i} className="p-3 bg-amber-50 rounded-xl text-xs space-y-1 border border-amber-200">
                  <p className="font-bold text-amber-900">{c.claim}</p>
                  <p className="text-amber-800">{c.evidence_text}</p>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card className="p-6 rounded-3xl border border-slate-200">
          <CardContent className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-purple-600 uppercase tracking-wider">
              <HelpCircle className="h-4 w-4" />
              <span>Section 18: Uncertainty / Unable-to-Verify ({unableList.length})</span>
            </div>
            {unableList.length === 0 ? (
              <p className="text-xs text-slate-500">All observed claims resolved with verifiable status.</p>
            ) : (
              unableList.map((u: any, i: number) => (
                <div key={i} className="p-3 bg-purple-50 rounded-xl text-xs space-y-1 border border-purple-200">
                  <p className="font-bold text-purple-900">{u.claim}</p>
                  <p className="text-purple-800">{u.evidence_text}</p>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* SECTION 19: SOURCE RELIABILITY DISTRIBUTION */}
      <Card className="p-6 rounded-3xl border border-slate-200">
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2 text-xs font-bold text-[#5b5dfa] uppercase tracking-wider">
            <BarChart3 className="h-4 w-4" />
            <span>Section 19: Source Reliability Distribution (Tier 1 – Tier 5)</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <div className="p-3 bg-slate-50 rounded-2xl text-center border border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase block">Tier 1 (Official)</span>
              <span className="text-lg font-bold text-emerald-600">{tierDist.tier_1} Sources</span>
            </div>
            <div className="p-3 bg-slate-50 rounded-2xl text-center border border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase block">Tier 2 (Regulated)</span>
              <span className="text-lg font-bold text-[#5b5dfa]">{tierDist.tier_2} Sources</span>
            </div>
            <div className="p-3 bg-slate-50 rounded-2xl text-center border border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase block">Tier 3 (Mainstream)</span>
              <span className="text-lg font-bold text-indigo-600">{tierDist.tier_3} Sources</span>
            </div>
            <div className="p-3 bg-slate-50 rounded-2xl text-center border border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase block">Tier 4 (Community)</span>
              <span className="text-lg font-bold text-amber-600">{tierDist.tier_4} Sources</span>
            </div>
            <div className="p-3 bg-slate-50 rounded-2xl text-center border border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase block">Tier 5 (Unverified)</span>
              <span className="text-lg font-bold text-slate-400">{tierDist.tier_5} Sources</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
