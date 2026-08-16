import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  History as HistoryIcon,
  Search,
  Building2,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import { researchService } from '../services/research';
import type { ResearchRun, ResearchStatus } from '../types';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/StatusBadge';
import { RiskBadge } from '../components/ui/RiskBadge';
import { EmptyState } from '../components/ui/EmptyState';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';

export const History: React.FC = () => {
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [filter, setFilter] = useState<'all' | ResearchStatus>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const fetchHistory = useCallback(async () => {
    try {
      const data = await researchService.getResearchHistory(50);
      setRuns(data);
    } catch (err) {
      console.warn('Could not load history:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    researchService
      .getResearchHistory(50)
      .then((data) => {
        if (isMounted) {
          setRuns(data);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.warn('Could not load history:', err);
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const handleRefresh = async () => {
    setIsLoading(true);
    await fetchHistory();
  };

  const filteredRuns = runs.filter((run) => {
    const matchesFilter = filter === 'all' || run.status === filter;
    const companyName = run.company?.name || '';
    const matchesSearch = companyName
      .toLowerCase()
      .includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="space-y-8 animate-fade-in pb-12 text-[#181534]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-indigo-50 border border-indigo-200/80 px-3.5 py-1 text-xs font-bold text-[#5b5dfa]">
            <HistoryIcon className="h-3.5 w-3.5" />
            <span>Audit Trail & Records</span>
          </div>
          <h1 className="mt-2 text-2xl sm:text-3xl font-extrabold tracking-tight text-[#181534]">
            Research History
          </h1>
          <p className="text-xs sm:text-sm font-medium text-slate-500">
            Review past company investigations, verification statuses, and intelligence reports.
          </p>
        </div>

        <Link to="/research">
          <Button variant="primary" size="md" className="finnova-btn-primary px-6" leftIcon={<Search className="h-4 w-4" />}>
            New Research Run
          </Button>
        </Link>
      </div>

      {/* Filters and Search Bar (Finnova White Pill Card) */}
      <div className="rounded-3xl bg-white border border-slate-200/80 p-4 shadow-sm">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:w-80">
            <input
              type="text"
              placeholder="Filter by company name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full rounded-full border border-slate-200 bg-white pl-4 pr-10 py-2.5 text-xs font-medium text-[#181534] placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#5b5dfa]"
            />
            <Search className="absolute right-3.5 top-3 h-3.5 w-3.5 text-slate-400" />
          </div>

          <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
            {(['all', 'completed', 'running', 'queued', 'failed'] as const).map((statusKey) => (
              <button
                key={statusKey}
                type="button"
                onClick={() => setFilter(statusKey)}
                className={`rounded-full px-3.5 py-1.5 text-xs font-bold capitalize transition-all ${
                  filter === statusKey
                    ? 'bg-[#5b5dfa] text-white shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200/80'
                }`}
              >
                {statusKey}
              </button>
            ))}

            <button
              type="button"
              onClick={handleRefresh}
              className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-slate-600 hover:bg-slate-200/80 transition-all"
              title="Refresh"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Runs Table Card */}
      <div className="rounded-[32px] bg-white border border-slate-200/80 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-6 space-y-4">
            <LoadingSkeleton variant="rect" count={4} />
          </div>
        ) : filteredRuns.length === 0 ? (
          <div className="p-10">
            <EmptyState
              icon={<Search className="h-8 w-8 text-[#5b5dfa]" />}
              title="No records found"
              description="No research runs match your current filter and search query."
              actionLabel="Launch Research"
              onAction={() => {
                window.location.href = '/research';
              }}
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-[#181534]">
              <thead className="bg-slate-50 border-b border-slate-100 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                <tr>
                  <th scope="col" className="px-6 py-4">Company</th>
                  <th scope="col" className="px-6 py-4">Status</th>
                  <th scope="col" className="px-6 py-4">Trust Score</th>
                  <th scope="col" className="px-6 py-4">Risk Level</th>
                  <th scope="col" className="px-6 py-4">Created</th>
                  <th scope="col" className="px-6 py-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredRuns.map((run) => (
                  <tr key={run.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-4 font-bold text-[#181534]">
                      <div className="flex items-center gap-2.5">
                        <Building2 className="h-4 w-4 text-[#5b5dfa] shrink-0" />
                        <span className="truncate max-w-[200px]">
                          {run.company?.name || 'Target Entity'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge
                        status={
                          run.status === 'completed'
                            ? 'verified'
                            : run.status === 'failed'
                            ? 'conflicting'
                            : 'unverified'
                        }
                        size="sm"
                      />
                    </td>
                    <td className="px-6 py-4 font-mono text-xs">
                      {run.trust_score?.score !== undefined ? (
                        <span className="font-extrabold text-[#5b5dfa]">
                          {run.trust_score.score.toFixed(1)} / 100
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <RiskBadge
                        level={run.trust_score?.risk_level || 'unknown'}
                        size="sm"
                      />
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-500 font-medium">
                      {new Date(run.created_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={
                          run.status === 'completed'
                            ? `/reports/${run.id}`
                            : `/research/${run.id}`
                        }
                      >
                        <Button
                          variant="secondary"
                          size="sm"
                          rightIcon={<ArrowRight className="h-3 w-3" />}
                        >
                          {run.status === 'completed' ? 'View Report' : 'Track'}
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
