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
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
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
      <div className="space-y-6">
        <LoadingSkeleton variant="rect" className="h-64 rounded-3xl" />
        <LoadingSkeleton variant="rect" className="h-64 rounded-2xl" />
      </div>
    );
  }

  if (!evidence) {
    return (
      <EmptyState
        icon={<FileCheck className="h-8 w-8 text-cyan-400" />}
        title="Evidence Record Not Found"
        description="The requested evidence artifact could not be retrieved from the evidence store."
        actionLabel="Back to History"
        onAction={() => {
          window.location.href = '/history';
        }}
      />
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8 animate-fade-in pb-12">
      {/* Header / Back */}
      <div className="flex items-center justify-between">
        <Link
          to="/history"
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-cyan-400 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Records</span>
        </Link>
        <div className="flex items-center gap-2">
          <StatusBadge status={evidence.verification_status} />
        </div>
      </div>

      {/* Main Evidence Card */}
      <Card glow="cyan" className="p-2 sm:p-4 border-slate-800">
        <CardHeader className="space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-cyan-400">
            <ShieldCheck className="h-4 w-4" />
            <span>Forensic Evidence Provenance</span>
          </div>
          <CardTitle className="text-2xl font-bold text-white">
            {evidence.claim}
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Extracted Evidence Text */}
          <div className="space-y-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Raw Extracted Evidence Snippet
            </span>
            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4 font-mono text-xs sm:text-sm text-slate-200 leading-relaxed overflow-x-auto">
              "{evidence.evidence_text}"
            </div>
          </div>

          {/* Source Provenance Info */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 sm:p-5 space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Source Provenance
              </span>
              <Badge variant="cyan" size="sm">
                Source Type: {evidence.source_type}
              </Badge>
            </div>

            <div className="space-y-2">
              <a
                href={evidence.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm font-semibold text-cyan-400 hover:text-cyan-300 hover:underline break-all"
              >
                <Globe className="h-4 w-4 shrink-0" />
                <span>{evidence.source_url}</span>
                <ExternalLink className="h-3.5 w-3.5 shrink-0" />
              </a>
              {evidence.source_title && (
                <p className="text-xs text-slate-400">
                  Title: {evidence.source_title}
                </p>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-3 border-t border-slate-800 text-xs text-slate-400">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-slate-500" />
                <span>
                  Observed At:{' '}
                  <strong className="text-slate-200">
                    {new Date(evidence.observed_at).toLocaleString()}
                  </strong>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Bot className="h-4 w-4 text-slate-500" />
                <span>
                  Collected By Agent:{' '}
                  <strong className="text-slate-200">
                    {evidence.agent_name || 'Verification Agent'}
                  </strong>
                </span>
              </div>
            </div>
          </div>

          {/* Quantitative Reliability Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400 font-semibold">
                  Source Reliability Score
                </span>
                <span className="font-mono font-bold text-cyan-400">
                  {((evidence.reliability_score || 0.85) * 100).toFixed(0)}%
                </span>
              </div>
              <ProgressBar
                value={(evidence.reliability_score || 0.85) * 100}
                color="cyan"
                showPercentage={false}
              />
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400 font-semibold">
                  Evidence Confidence Score
                </span>
                <span className="font-mono font-bold text-emerald-400">
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
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center gap-2 text-xs font-mono text-slate-400 truncate">
              <Hash className="h-4 w-4 text-cyan-400 shrink-0" />
              <span className="text-slate-500">SHA-256:</span>
              <span className="truncate">{evidence.content_hash}</span>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
