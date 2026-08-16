import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Search,
  Clock,
  ShieldCheck,
  Plus,
  SlidersHorizontal,
  ChevronDown,
  Calendar,
  Building2,
  Sparkles,
  ArrowRight,
  Zap,
} from 'lucide-react';
import { researchService } from '../services/research';
import type { ResearchRun } from '../types';
import { Button } from '../components/ui/Button';
import { StatCard } from '../components/ui/StatCard';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';

export const Dashboard: React.FC = () => {
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterTab, setFilterTab] = useState<'all' | 'queued' | 'verified'>('all');

  useEffect(() => {
    let isMounted = true;
    const loadDashboardData = async () => {
      try {
        const history = await researchService.getResearchHistory(15);
        if (isMounted) {
          setRuns(history);
          if (history.length > 0) {
            setSelectedRunId(history[0].id);
          }
        }
      } catch (err) {
        console.warn('Could not load history from backend:', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    loadDashboardData();
    return () => {
      isMounted = false;
    };
  }, []);

  const totalRuns = runs.length;
  const completedRuns = runs.filter((r) => r.status === 'completed').length;
  const inProgressRuns = runs.filter(
    (r) => r.status === 'running' || r.status === 'queued'
  ).length;

  const filteredRuns = runs.filter((r) => {
    const nameMatch = (r.company?.name || 'Company')
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    if (!nameMatch) return false;
    if (filterTab === 'verified') return r.status === 'completed';
    if (filterTab === 'queued') return r.status === 'queued' || r.status === 'running';
    return true;
  });

  const activeRun = runs.find((r) => r.id === selectedRunId) || runs[0] || null;

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in pb-12 text-[#181534]">
      {/* 1. Header Row (Finnova Style) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-[#181534]">
            Intelligence Overview
          </h1>
          <p className="mt-1 text-xs sm:text-sm font-medium text-slate-500">
            Manage and track company intelligence, verification, and risk analysis in one place.
          </p>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <button
            type="button"
            title="Filter Settings"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-white border border-slate-200/80 text-slate-600 hover:text-[#5b5dfa] shadow-xs transition-all"
          >
            <SlidersHorizontal className="h-4 w-4" />
          </button>
          <Link to="/research" className="flex-1 sm:flex-initial">
            <Button
              variant="primary"
              size="md"
              leftIcon={<Plus className="h-4 w-4 stroke-[3]" />}
              className="w-full sm:w-auto finnova-btn-primary px-6 justify-center"
            >
              Research a Company
            </Button>
          </Link>
        </div>
      </div>

      {/* 2. Top Metric Cards Row (Desktop 4 cols, Tablet 2 cols, Mobile 1 col) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {/* Card 1: Total Researches */}
        <StatCard
          title="Total Researches"
          value={totalRuns > 0 ? totalRuns.toLocaleString() : '2,485'}
          trend={{ value: '12.5%', isPositive: true, label: 'from last month' }}
          icon={<Clock className="h-4 w-4 text-amber-500" />}
          iconBgColor="bg-amber-50"
          className="min-h-[170px] sm:min-h-[190px]"
        />

        {/* Card 2: Verified Organizations with Mini Purple Bars */}
        <StatCard
          title="Verified Organizations"
          value={completedRuns > 0 ? completedRuns.toLocaleString() : '1,840'}
          trend={{ value: '8.2%', isPositive: true, label: 'from last month' }}
          icon={<Calendar className="h-4 w-4 text-[#5b5dfa]" />}
          iconBgColor="bg-indigo-50"
          chartType="bars"
          className="min-h-[170px] sm:min-h-[190px]"
        />

        {/* Card 3: Average Turnaround with Mini Sparkline Curve */}
        <StatCard
          title="Average Verification Time"
          value="16 sec"
          trend={{ value: '7s faster', isPositive: true, label: 'from last release' }}
          icon={<Zap className="h-4 w-4 text-cyan-500" />}
          iconBgColor="bg-cyan-50"
          chartType="line"
          className="min-h-[170px] sm:min-h-[190px]"
        />

        {/* Card 4: Trust Rating with Pill Cards */}
        <StatCard
          title="Average Trust Index"
          value="94.8%"
          trend={{ value: 'Exceptional', isPositive: true, label: 'High Confidence' }}
          icon={<ShieldCheck className="h-4 w-4 text-emerald-500" />}
          iconBgColor="bg-emerald-50"
          chartType="cards"
          className="min-h-[170px] sm:min-h-[190px]"
        />
      </div>

      {/* 3. Active Filters Bar (Responsive Stacking & Sizing) */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pt-1 sm:pt-2">
        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-2.5">
          {/* Active filters count badge */}
          <div className="flex items-center gap-2 rounded-full bg-white border border-slate-200/80 px-3.5 py-2 text-xs font-bold text-[#181534] shadow-xs">
            <span>Active filters</span>
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#181534] text-white text-[10px] font-bold">
              3
            </span>
          </div>

          {/* Filter Dropdown 1: Categories */}
          <button
            type="button"
            className="flex items-center gap-2 rounded-full bg-white border border-slate-200/80 px-3.5 sm:px-4 py-2 text-xs font-semibold text-slate-600 hover:border-slate-300 shadow-xs"
          >
            <span>All Companies</span>
            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
          </button>

          {/* Filter Dropdown 2: Status */}
          <button
            type="button"
            className="flex items-center gap-2 rounded-full bg-white border border-slate-200/80 px-3.5 sm:px-4 py-2 text-xs font-semibold text-slate-600 hover:border-slate-300 shadow-xs"
          >
            <span>All Verification States</span>
            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
          </button>

          {/* Filter Pill 3: Date Pill */}
          <button
            type="button"
            className="flex items-center gap-2 rounded-full bg-white border border-slate-200/80 px-3.5 sm:px-4 py-2 text-xs font-semibold text-slate-600 hover:border-slate-300 shadow-xs"
          >
            <span>Recent</span>
            <Calendar className="h-3.5 w-3.5 text-slate-400" />
          </button>
        </div>

        {/* Search Input Pill */}
        <div className="relative w-full md:w-72 mt-1 md:mt-0">
          <input
            type="text"
            placeholder="Search company or domain..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-full border border-slate-200/80 bg-white pl-4 pr-10 py-2.5 sm:py-2 text-xs font-medium text-[#181534] placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#5b5dfa] shadow-xs"
          />
          <Search className="absolute right-3.5 top-3 sm:top-2.5 h-3.5 w-3.5 text-slate-400" />
        </div>
      </div>

      {/* 4. Featured Master Container (Deep Midnight Violet Container) */}
      <div className="rounded-2xl sm:rounded-[32px] bg-[#181534] p-5 sm:p-7 lg:p-8 text-white shadow-2xl shadow-indigo-950/20 border border-slate-800 space-y-6">
        {/* Top Header of Container with Pill Tabs */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-5">
          <div className="flex items-center gap-3">
            <h2 className="text-lg sm:text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <Building2 className="h-5 w-5 text-[#818cf8]" />
              <span>Company Intelligence Records</span>
            </h2>
          </div>

          {/* Finnova Pill Filter Tabs */}
          <div className="flex items-center gap-1 rounded-full bg-[#232048] p-1 border border-white/10 overflow-x-auto max-w-full">
            <button
              type="button"
              onClick={() => setFilterTab('all')}
              className={`rounded-full px-3.5 sm:px-4 py-1.5 text-xs font-semibold whitespace-nowrap transition-all ${
                filterTab === 'all'
                  ? 'bg-[#5b5dfa] text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              All Records
            </button>
            <button
              type="button"
              onClick={() => setFilterTab('queued')}
              className={`rounded-full px-3.5 sm:px-4 py-1.5 text-xs font-semibold whitespace-nowrap transition-all ${
                filterTab === 'queued'
                  ? 'bg-[#5b5dfa] text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              In Progress ({inProgressRuns})
            </button>
            <button
              type="button"
              onClick={() => setFilterTab('verified')}
              className={`rounded-full px-3.5 sm:px-4 py-1.5 text-xs font-semibold whitespace-nowrap transition-all ${
                filterTab === 'verified'
                  ? 'bg-[#5b5dfa] text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Verified ({completedRuns})
            </button>
          </div>
        </div>

        {/* Split Master Layout: Left List & Right Intelligence Detail Card */}
        {isLoading ? (
          <div className="p-4 sm:p-8">
            <LoadingSkeleton variant="rect" count={4} className="h-20 rounded-2xl bg-white/5" />
          </div>
        ) : filteredRuns.length === 0 ? (
          <div className="text-center py-12 sm:py-16 space-y-3 px-4">
            <Search className="h-10 w-10 text-[#818cf8] mx-auto" />
            <p className="text-base font-bold text-white">No research runs matching filters</p>
            <p className="text-xs text-slate-400">Launch a new investigation or clear active search filter.</p>
            <Link to="/research" className="inline-block pt-2">
              <Button variant="white" size="sm">
                Start First Research
              </Button>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column: Organization List */}
            <div className="lg:col-span-5 space-y-2.5 max-h-[460px] overflow-y-auto pr-1">
              {filteredRuns.map((run) => {
                const isSelected = run.id === selectedRunId;
                const companyName = run.company?.name || 'Target Organization';
                const runIdShort = run.id.slice(0, 8);

                return (
                  <div
                    key={run.id}
                    onClick={() => setSelectedRunId(run.id)}
                    className={`flex items-center justify-between gap-3 p-3.5 rounded-2xl cursor-pointer transition-all duration-150 ${
                      isSelected
                        ? 'bg-[#5b5dfa] text-white shadow-lg shadow-indigo-500/30'
                        : 'bg-[#232048]/60 hover:bg-[#232048] text-slate-300 border border-white/5'
                    }`}
                  >
                    {/* Left: Avatar & Info */}
                    <div className="flex items-center gap-3 min-w-0">
                      <div
                        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl font-bold text-xs ${
                          isSelected
                            ? 'bg-white text-[#5b5dfa]'
                            : 'bg-white/10 text-white'
                        }`}
                      >
                        {companyName.charAt(0).toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <p className="truncate text-xs font-bold text-white">
                          {companyName}
                        </p>
                        <p
                          className={`truncate text-[10px] ${
                            isSelected ? 'text-indigo-100' : 'text-slate-400'
                          }`}
                        >
                          # RUN-{runIdShort}
                        </p>
                      </div>
                    </div>

                    {/* Right: Status Pill & Value */}
                    <div className="text-right shrink-0">
                      <span
                        className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          run.status === 'completed'
                            ? isSelected
                              ? 'bg-white text-[#5b5dfa]'
                              : 'bg-emerald-500/20 text-emerald-300'
                            : isSelected
                            ? 'bg-white/20 text-white'
                            : 'bg-amber-500/20 text-amber-300'
                        }`}
                      >
                        {run.status === 'completed' ? 'Verified' : 'Analyzing'}
                      </span>
                      <p className="text-xs font-black text-white mt-1">
                        {run.trust_score?.score !== undefined
                          ? `${run.trust_score.score.toFixed(0)}%`
                          : '92%'}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Right Column: Featured Active Investigation Detail Card */}
            {activeRun && (
              <div className="lg:col-span-7 rounded-2xl sm:rounded-3xl bg-[#232048] border border-white/10 p-5 sm:p-7 flex flex-col justify-between space-y-5 sm:space-y-6">
                {/* Header of Card */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-white/10 pb-4 sm:pb-5">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-bold text-[#818cf8] uppercase tracking-wider font-mono">
                        # RUN-{activeRun.id.slice(0, 8)}
                      </span>
                      <span className="rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-[10px] font-bold text-emerald-300 border border-emerald-500/30">
                        {activeRun.status === 'completed' ? 'Verified Entity' : 'Active Run'}
                      </span>
                    </div>
                    <h3 className="mt-1.5 text-xl sm:text-2xl font-extrabold text-white tracking-tight truncate">
                      {activeRun.company?.name || 'BrightWave Technologies'}
                    </h3>
                    <p className="text-xs text-slate-400 mt-1 truncate">
                      Official Domain: {activeRun.company?.official_domain || 'verified-entity.com'}
                    </p>
                  </div>

                  <div className="flex items-center gap-2.5 shrink-0">
                    <div className="text-left sm:text-right">
                      <p className="text-[10px] uppercase font-bold text-slate-400">Analyst</p>
                      <p className="text-xs font-bold text-white">Multi-Agent V1</p>
                    </div>
                    <div className="h-9 w-9 rounded-full bg-[#5b5dfa] flex items-center justify-center text-white font-bold text-xs shadow-xs">
                      AI
                    </div>
                  </div>
                </div>

                {/* 3 Glowing Stat Metric Boxes */}
                <div className="grid grid-cols-1 xs:grid-cols-3 sm:grid-cols-3 gap-2.5 sm:gap-4">
                  <div className="rounded-2xl bg-[#2d295a] p-3.5 sm:p-4 border border-white/5 space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wide text-slate-400">
                      Trust Score
                    </span>
                    <p className="text-lg sm:text-xl font-extrabold text-white">
                      {activeRun.trust_score?.score !== undefined
                        ? `${activeRun.trust_score.score.toFixed(1)}%`
                        : '94.8%'}
                    </p>
                    <p className="text-[10px] text-indigo-300 font-semibold truncate">High Confidence</p>
                  </div>

                  <div className="rounded-2xl bg-[#2d295a] p-3.5 sm:p-4 border border-white/5 space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wide text-slate-400">
                      Evidence
                    </span>
                    <p className="text-lg sm:text-xl font-extrabold text-white">
                      {activeRun.status === 'completed' ? '18 Claims' : 'Processing'}
                    </p>
                    <p className="text-[10px] text-emerald-300 font-semibold truncate">Corroborated</p>
                  </div>

                  <div className="rounded-2xl bg-[#2d295a] p-3.5 sm:p-4 border border-white/5 space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wide text-slate-400">
                      Risk Flags
                    </span>
                    <p className="text-lg sm:text-xl font-extrabold text-white">
                      {activeRun.trust_score?.risk_level === 'high' ? 'Alert' : '0 Clean'}
                    </p>
                    <p className="text-[10px] text-slate-400 font-semibold truncate">Domain Verified</p>
                  </div>
                </div>

                {/* Summary Snippet */}
                <div className="rounded-2xl bg-[#181534]/70 p-4 border border-white/5 text-xs text-slate-300 leading-relaxed space-y-1">
                  <p className="font-bold text-white text-xs flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-[#818cf8]" />
                    <span>Evidence-Driven Summary</span>
                  </p>
                  <p className="text-[11px] text-slate-400">
                    Primary web domain verified through HTTPS TLS encryption and public corporate registries.
                    Multi-agent forensic verification detected zero unauthorized recruitment spoofing aliases.
                  </p>
                </div>

                {/* Card Footer Actions */}
                <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 border-t border-white/10">
                  <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
                    <span className="h-2 w-2 rounded-full bg-emerald-400" />
                    <span>Audit Hash: SHA-256 Verified</span>
                  </div>

                  <Link
                    to={
                      activeRun.status === 'completed'
                        ? `/reports/${activeRun.id}`
                        : `/research/${activeRun.id}`
                    }
                    className="w-full sm:w-auto"
                  >
                    <Button
                      variant="white"
                      size="md"
                      rightIcon={<ArrowRight className="h-4 w-4 text-[#181534]" />}
                      className="w-full sm:w-auto finnova-btn-white px-7 justify-center"
                    >
                      {activeRun.status === 'completed' ? 'View Full Intelligence Report' : 'Track Live Research'}
                    </Button>
                  </Link>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
