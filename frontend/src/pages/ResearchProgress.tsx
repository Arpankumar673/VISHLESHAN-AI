import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Loader2,
  CheckCircle2,
  Clock,
  XCircle,
  Building2,
  ArrowRight,
  FileText,
  Search,
  Scale,
} from 'lucide-react';
import { researchService } from '../services/research';
import type { ResearchRun, ResearchAgentStep } from '../types';
import { Button } from '../components/ui/Button';
import { ProgressBar } from '../components/ui/ProgressBar';
import { StatusBadge } from '../components/ui/StatusBadge';
import { RiskBadge } from '../components/ui/RiskBadge';

export const ResearchProgress: React.FC = () => {
  const { runId } = useParams<{ runId: string }>();

  const [run, setRun] = useState<ResearchRun | null>(null);

  const initialSteps: ResearchAgentStep[] = [
    {
      agentName: 'orchestrator',
      label: 'Orchestrator Agent',
      description: 'Routing research requests and coordinating workflow lifecycle.',
      status: 'completed',
    },
    {
      agentName: 'company_research',
      label: 'Company Research Agent',
      description: 'Extracting company overview, industry, locations, and public metadata.',
      status: 'completed',
    },
    {
      agentName: 'verification',
      label: 'Verification Agent',
      description: 'Cross-verifying domain provenance, MCA/SEC records, and certifications.',
      status: 'running',
    },
    {
      agentName: 'news_hiring',
      label: 'News & Hiring Agent',
      description: 'Gathering press releases, hiring volumes, open roles, and announcements.',
      status: 'pending',
    },
    {
      agentName: 'technology_reputation',
      label: 'Technology & Reputation Agent',
      description: 'Evaluating tech stack signals, engineering presence, and public reviews.',
      status: 'pending',
    },
    {
      agentName: 'risk_analysis',
      label: 'Risk Analysis Agent',
      description: 'Evaluating deceptive recruitment patterns and domain spoofing alerts.',
      status: 'pending',
    },
    {
      agentName: 'evidence_fusion',
      label: 'Evidence & Trust Engine',
      description: 'Executing deterministic Python fusion and reproducible trust scoring.',
      status: 'pending',
    },
    {
      agentName: 'report_agent',
      label: 'Report Agent',
      description: 'Assembling structured 13-section Company Intelligence Report.',
      status: 'pending',
    },
  ];

  const [agentSteps, setAgentSteps] = useState<ResearchAgentStep[]>(initialSteps);

  useEffect(() => {
    if (!runId) return;

    let isMounted = true;

    const fetchStatus = async () => {
      try {
        const data = await researchService.getResearchRun(runId);
        if (isMounted) {
          setRun(data);

          if (data.status === 'completed') {
            setAgentSteps((prev) =>
              prev.map((step) => ({ ...step, status: 'completed' }))
            );
          } else if (data.status === 'running') {
            setAgentSteps((prev) =>
              prev.map((step, idx) => {
                if (idx < 3) return { ...step, status: 'completed' };
                if (idx === 3) return { ...step, status: 'running' };
                return { ...step, status: 'pending' };
              })
            );
          } else if (data.status === 'failed') {
            setAgentSteps((prev) =>
              prev.map((step, idx) => {
                if (idx < 2) return { ...step, status: 'completed' };
                if (idx === 2) return { ...step, status: 'failed' };
                return { ...step, status: 'pending' };
              })
            );
          }
        }
      } catch (err: unknown) {
        if (isMounted) {
          console.warn('Could not poll research run status:', err);
        }
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 4000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [runId]);

  const completedSteps = agentSteps.filter((s) => s.status === 'completed').length;
  const progressPercent = Math.round((completedSteps / agentSteps.length) * 100);

  return (
    <div className="mx-auto max-w-4xl space-y-6 sm:space-y-8 animate-fade-in pb-12 text-[#181534]">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-5 sm:pb-6">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-xs font-bold text-[#5b5dfa]">
            <Search className="h-3.5 w-3.5" />
            <span className="truncate">Research Run: {runId?.slice(0, 8)}...</span>
          </div>
          <h1 className="mt-1 text-2xl sm:text-3xl font-extrabold tracking-tight text-[#181534] flex items-center gap-2.5 sm:gap-3 truncate">
            <Building2 className="h-6 w-6 sm:h-7 sm:w-7 text-[#5b5dfa] shrink-0" />
            <span className="truncate">{run?.company?.name || 'Company Intelligence Investigation'}</span>
          </h1>
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:gap-3 shrink-0">
          <StatusBadge
            status={
              run?.status === 'completed'
                ? 'verified'
                : run?.status === 'failed'
                ? 'conflicting'
                : 'unverified'
            }
          />
          {run?.trust_score?.risk_level && (
            <RiskBadge level={run.trust_score.risk_level} />
          )}
        </div>
      </div>

      {/* Progress Bar Card (Finnova White Card) */}
      <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-7 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2.5">
            {run?.status === 'completed' ? (
              <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" />
            ) : run?.status === 'failed' ? (
              <XCircle className="h-5 w-5 text-rose-500 shrink-0" />
            ) : (
              <Loader2 className="h-5 w-5 animate-spin text-[#5b5dfa] shrink-0" />
            )}
            <span className="font-bold text-sm sm:text-base text-[#181534]">
              {run?.status === 'completed'
                ? 'Research Run Completed'
                : run?.status === 'failed'
                ? 'Research Run Terminated with Error'
                : 'Multi-Agent Investigation in Progress...'}
            </span>
          </div>
          <span className="text-xs font-mono font-bold text-slate-400">
            {completedSteps} of {agentSteps.length} Agents Completed
          </span>
        </div>

        <ProgressBar
          value={progressPercent}
          color={
            run?.status === 'failed'
              ? 'rose'
              : run?.status === 'completed'
              ? 'emerald'
              : 'cyan'
          }
          showPercentage
        />

        {run?.status === 'completed' && (
          <div className="pt-3 flex justify-end">
            <Link to={`/reports/${run.id}`} className="w-full sm:w-auto">
              <Button
                variant="primary"
                size="md"
                leftIcon={<FileText className="h-4 w-4" />}
                rightIcon={<ArrowRight className="h-4 w-4" />}
                className="w-full sm:w-auto finnova-btn-primary px-7 justify-center"
              >
                View Full Intelligence Report
              </Button>
            </Link>
          </div>
        )}
      </div>

      {/* Multi-Agent Steps List (Finnova Card) */}
      <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-7 shadow-sm space-y-4">
        <div className="border-b border-slate-100 pb-3 sm:pb-4">
          <h2 className="text-base font-bold text-[#181534] flex items-center gap-2">
            <Scale className="h-4 w-4 text-[#5b5dfa]" />
            <span>Agent Pipeline & Forensic Execution</span>
          </h2>
        </div>

        <div className="divide-y divide-slate-100">
          {agentSteps.map((step, index) => (
            <div
              key={step.agentName}
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 p-3.5 sm:p-4 hover:bg-slate-50/80 rounded-2xl transition-colors"
            >
              <div className="flex items-start gap-3 sm:gap-3.5">
                <div className="flex h-7 w-7 sm:h-8 sm:w-8 shrink-0 items-center justify-center rounded-xl bg-indigo-50 font-bold text-xs text-[#5b5dfa]">
                  {index + 1}
                </div>
                <div className="space-y-0.5 sm:space-y-1">
                  <p className="text-xs sm:text-sm font-bold text-[#181534]">
                    {step.label}
                  </p>
                  <p className="text-[11px] sm:text-xs text-slate-500 font-medium leading-relaxed">
                    {step.description}
                  </p>
                </div>
              </div>

              <div className="self-end sm:self-center shrink-0 flex items-center">
                {step.status === 'completed' ? (
                  <span className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 sm:px-3 py-1 rounded-full border border-emerald-200/80">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Done</span>
                  </span>
                ) : step.status === 'running' ? (
                  <span className="inline-flex items-center gap-1.5 text-xs font-bold text-[#5b5dfa] bg-indigo-50 px-2.5 sm:px-3 py-1 rounded-full border border-indigo-200/80 animate-pulse">
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    <span>Executing</span>
                  </span>
                ) : step.status === 'failed' ? (
                  <span className="inline-flex items-center gap-1.5 text-xs font-bold text-rose-700 bg-rose-50 px-2.5 sm:px-3 py-1 rounded-full border border-rose-200/80">
                    <XCircle className="h-3.5 w-3.5" />
                    <span>Failed</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 bg-slate-100 px-2.5 sm:px-3 py-1 rounded-full">
                    <Clock className="h-3.5 w-3.5" />
                    <span>Queued</span>
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
