import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  FileCheck,
  Globe,
  Calendar,
  ExternalLink,
  ShieldCheck,
  ArrowLeft,
  Hash,
  Bot,
} from 'lucide-react';
import { evidenceService } from '../services/evidence';
import type { Evidence } from '../types';
import { StatusBadge } from '../components/ui/StatusBadge';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ProgressBar } from '../components/ui/ProgressBar';

export const EvidenceExplorer: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!id) return;

    let isMounted = true;
    const fetchEvidence = async () => {
      try {
        const data = await evidenceService.getEvidence(id);
        if (isMounted) setEvidence(data);
      } catch (err) {
        console.warn('Could not load evidence:', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchEvidence();
    return () => {
      isMounted = false;
    };
  }, [id]);

  if (isLoading) {
    return (
      <div className="space-y-6 pb-12">
        <LoadingSkeleton variant="rect" className="h-64 rounded-3xl" />
        <LoadingSkeleton variant="rect" className="h-64 rounded-2xl" />
      </div>
    );
  }

  if (!evidence) {
    return (
      <div className="pb-12">
        <EmptyState
          icon={<FileCheck className="h-8 w-8 text-[#5b5dfa]" />}
          title="Evidence Record Not Found"
          description="The requested evidence artifact could not be retrieved from the evidence store."
          actionLabel="Back to History"
          onAction={() => {
            window.location.href = '/history';
          }}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 sm:space-y-8 animate-fade-in pb-12 text-[#181534]">
      {/* Header / Back */}
      <div className="flex flex-col xs:flex-row items-start xs:items-center justify-between gap-3">
        <Link
          to="/history"
          className="inline-flex items-center gap-2 text-xs font-bold text-slate-500 hover:text-[#5b5dfa] transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Records</span>
        </Link>
        <div className="flex items-center gap-2">
          <StatusBadge status={evidence.verification_status} />
        </div>
      </div>

      {/* Main Evidence Card */}
      <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 shadow-sm space-y-6">
        <div className="border-b border-slate-100 pb-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-[#5b5dfa]">
            <ShieldCheck className="h-4 w-4" />
            <span>Forensic Evidence Provenance</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-[#181534] tracking-tight">
            {evidence.claim}
          </h1>
        </div>

        <div className="space-y-6">
          {/* Extracted Evidence Text */}
          <div className="space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Raw Extracted Evidence Snippet
            </span>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 font-mono text-xs sm:text-sm text-slate-700 leading-relaxed overflow-x-auto">
              "{evidence.evidence_text}"
            </div>
          </div>

          {/* Source Provenance Info */}
          <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4 sm:p-5 space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Source Provenance
              </span>
              <Badge variant="purple" size="sm">
                Source Type: {evidence.source_type}
              </Badge>
            </div>

            <div className="space-y-2">
              <a
                href={evidence.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-xs sm:text-sm font-semibold text-[#5b5dfa] hover:underline break-all"
              >
                <Globe className="h-4 w-4 shrink-0" />
                <span>{evidence.source_url}</span>
                <ExternalLink className="h-3.5 w-3.5 shrink-0" />
              </a>
              {evidence.source_title && (
                <p className="text-xs text-slate-500 font-medium">
                  Title: {evidence.source_title}
                </p>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3 border-t border-slate-200 text-xs text-slate-500">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-slate-400 shrink-0" />
                <span className="truncate">
                  Observed:{' '}
                  <strong className="text-[#181534]">
                    {new Date(evidence.observed_at).toLocaleString()}
                  </strong>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Bot className="h-4 w-4 text-slate-400 shrink-0" />
                <span className="truncate">
                  Agent:{' '}
                  <strong className="text-[#181534]">
                    {evidence.agent_name || 'Verification Agent'}
                  </strong>
                </span>
              </div>
            </div>
          </div>

          {/* Quantitative Reliability Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-2">
              <div className="flex justify-between text-xs font-bold">
                <span className="text-slate-500">Source Reliability</span>
                <span className="font-mono text-[#5b5dfa]">
                  {((evidence.reliability_score || 0.85) * 100).toFixed(0)}%
                </span>
              </div>
              <ProgressBar
                value={(evidence.reliability_score || 0.85) * 100}
                color="purple"
                showPercentage={false}
              />
            </div>

            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-2">
              <div className="flex justify-between text-xs font-bold">
                <span className="text-slate-500">Evidence Confidence</span>
                <span className="font-mono text-emerald-600">
                  {((evidence.confidence_score || 0.9) * 100).toFixed(0)}%
                </span>
              </div>
              <ProgressBar
                value={(evidence.confidence_score || 0.9) * 100}
                color="emerald"
                showPercentage={false}
              />
            </div>
          </div>

          {/* Cryptographic Content Hash */}
          {evidence.content_hash && (
            <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 flex items-center gap-2 text-xs font-mono text-slate-600 truncate">
              <Hash className="h-4 w-4 text-[#5b5dfa] shrink-0" />
              <span className="text-slate-400 shrink-0">SHA-256:</span>
              <span className="truncate">{evidence.content_hash}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
