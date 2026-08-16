import React from 'react';
import { ExternalLink, ShieldCheck, Globe, Calendar } from 'lucide-react';
import type { SourceType } from '../../types';
import { Badge } from './Badge';

export interface SourceReferenceProps {
  index?: number;
  url: string;
  title?: string;
  sourceType?: SourceType;
  reliabilityScore?: number | null;
  observedAt?: string;
  compact?: boolean;
  className?: string;
}

const getDomain = (urlStr: string): string => {
  try {
    const parsed = new URL(urlStr);
    return parsed.hostname.replace(/^www\./, '');
  } catch {
    return urlStr;
  }
};

export const SourceReference: React.FC<SourceReferenceProps> = ({
  index,
  url,
  title,
  sourceType,
  reliabilityScore,
  observedAt,
  compact = false,
  className = '',
}) => {
  const domain = getDomain(url);

  const sourceTypeLabels: Record<
    SourceType,
    { label: string; variant: 'emerald' | 'cyan' | 'blue' | 'amber' | 'purple' | 'slate' }
  > = {
    government: { label: 'Government', variant: 'emerald' },
    regulator: { label: 'Regulator', variant: 'emerald' },
    certification_body: { label: 'Cert Authority', variant: 'emerald' },
    official_company: { label: 'Official Site', variant: 'cyan' },
    official_careers: { label: 'Careers Portal', variant: 'cyan' },
    official_announcement: { label: 'Announcement', variant: 'blue' },
    news: { label: 'News Media', variant: 'blue' },
    professional_network: { label: 'Prof. Network', variant: 'amber' },
    employee_review: { label: 'Review Platform', variant: 'amber' },
    forum: { label: 'Public Forum', variant: 'purple' },
    blog: { label: 'Blog', variant: 'purple' },
    other: { label: 'Web Source', variant: 'slate' },
  };

  if (compact) {
    return (
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        title={`${title || domain} — Source Provenance`}
        className={`inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 hover:text-cyan-300 hover:underline transition-colors ${className}`}
      >
        {index !== undefined && (
          <span className="rounded bg-cyan-950/80 px-1.5 py-0.5 border border-cyan-800 text-[10px] text-cyan-300">
            [{index}]
          </span>
        )}
        <span className="truncate max-w-[140px]">{domain}</span>
        <ExternalLink className="h-3 w-3 inline" />
      </a>
    );
  }

  const sourceConfig = sourceType ? sourceTypeLabels[sourceType] : undefined;

  return (
    <div
      className={`group flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/40 hover:bg-slate-900 transition-all ${className}`}
    >
      <div className="flex items-start gap-3 min-w-0">
        {index !== undefined && (
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-xs font-bold text-cyan-400">
            {index}
          </span>
        )}
        <div className="min-w-0">
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-100 hover:text-cyan-300 transition-colors group-hover:text-cyan-300"
          >
            <span className="truncate">{title || domain}</span>
            <ExternalLink className="h-3.5 w-3.5 shrink-0 text-slate-400 group-hover:text-cyan-300" />
          </a>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-400">
            <span className="inline-flex items-center gap-1 font-mono text-[11px] text-slate-400">
              <Globe className="h-3 w-3 text-slate-500" />
              {domain}
            </span>
            {observedAt && (
              <span className="inline-flex items-center gap-1 text-[11px] text-slate-400">
                <Calendar className="h-3 w-3 text-slate-500" />
                {new Date(observedAt).toLocaleDateString(undefined, {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                })}
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 self-start sm:self-center shrink-0">
        {sourceConfig && (
          <Badge variant={sourceConfig.variant} size="sm">
            {sourceConfig.label}
          </Badge>
        )}
        {reliabilityScore !== undefined && reliabilityScore !== null && (
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-800 px-2 py-0.5 text-[10px] font-medium text-slate-300 border border-slate-700">
            <ShieldCheck className="h-3 w-3 text-cyan-400" />
            {(reliabilityScore * 100).toFixed(0)}% Rel.
          </span>
        )}
      </div>
    </div>
  );
};
