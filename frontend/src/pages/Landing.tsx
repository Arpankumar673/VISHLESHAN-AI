import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  Search,
  Scale,
  FileCheck2,
  ArrowRight,
  Sparkles,
  Layers,
  Globe,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useAuth } from '../hooks/useAuth';

export const Landing: React.FC = () => {
  const { user } = useAuth();

  const features = [
    {
      icon: ShieldCheck,
      title: 'Evidence-Backed Intelligence',
      description:
        'Every factual claim links directly to a verifiable public source URL, timestamp, and reliability score.',
    },
    {
      icon: FileCheck2,
      title: 'Verification & Provenance',
      description:
        'Authoritative checks across government registries, official company domains, and regulatory bodies.',
    },
    {
      icon: Scale,
      title: 'Deterministic Trust & Risk',
      description:
        'Mathematical scoring algorithms in Python provide explainable, reproducible trust and risk signals.',
    },
    {
      icon: Layers,
      title: 'Multi-Agent Research Pipeline',
      description:
        'Specialized agents handle identity, registration, news, hiring signals, technology, and risk forensics.',
    },
  ];

  const verificationStates = [
    {
      status: 'verified' as const,
      desc: 'Corroborated by Tier-1 government or official authoritative records.',
    },
    {
      status: 'unverified' as const,
      desc: 'Observed claim without sufficient official public documentation.',
    },
    {
      status: 'conflicting' as const,
      desc: 'Contradictory information identified across different public sources.',
    },
    {
      status: 'unable_to_verify' as const,
      desc: 'Authoritative data is unavailable; communicated with explicit uncertainty.',
    },
  ];

  return (
    <div className="relative min-h-screen bg-[#f0f2f8] text-[#181534] selection:bg-[#5b5dfa]/20 selection:text-[#5b5dfa] overflow-hidden pb-16">
      {/* Background ambient lighting */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[400px] sm:h-[600px] w-[500px] sm:w-[900px] rounded-full bg-[#5b5dfa]/5 blur-[100px] sm:blur-[140px]" />
        <div className="absolute top-3/4 left-1/3 -translate-x-1/2 -translate-y-1/2 h-[300px] sm:h-[500px] w-[400px] sm:w-[700px] rounded-full bg-[#7c3aed]/5 blur-[100px] sm:blur-[140px]" />
      </div>

      {/* Hero Section: 2-Column Desktop Grid / 1-Column Mobile Stack */}
      <section className="relative mx-auto w-full max-w-[1440px] px-4 sm:px-6 lg:px-8 xl:px-10 pt-6 sm:pt-10 lg:pt-16 pb-12 sm:pb-16 lg:pb-20">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
          {/* Left Column (Hero Content): lg:col-span-7 */}
          <div className="lg:col-span-7 space-y-5 sm:space-y-6 text-left">
            {/* Pill Badge */}
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200/80 bg-indigo-50 px-3.5 sm:px-4 py-1.5 text-xs font-bold text-[#5b5dfa] shadow-xs">
              <Sparkles className="h-3.5 w-3.5 shrink-0" />
              <span>AI-Powered Corporate Intelligence Platform</span>
            </div>

            {/* Fluid Responsive Heading */}
            <h1 className="text-3xl xs:text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-[#181534] leading-[1.12]">
              Verify Organizations with{' '}
              <span className="bg-gradient-to-r from-[#5b5dfa] via-[#7c3aed] to-[#38bdf8] bg-clip-text text-transparent">
                Deterministic Evidence
              </span>
            </h1>

            {/* Description */}
            <p className="text-sm sm:text-base lg:text-lg text-slate-500 font-medium leading-relaxed max-w-2xl">
              Research, verify and analyze companies using evidence-backed multi-agent intelligence,
              reproducible trust scoring, and recruitment risk forensics.
            </p>

            {/* Responsive CTA Button Grid */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4 pt-2">
              <Link to={user ? '/research' : '/login'} className="w-full sm:w-auto">
                <Button
                  variant="primary"
                  size="lg"
                  className="w-full sm:w-auto px-8 finnova-btn-primary justify-center text-sm sm:text-base"
                  leftIcon={<Search className="h-4 w-4 sm:h-5 sm:w-5" />}
                  rightIcon={<ArrowRight className="h-4 w-4" />}
                >
                  Start Company Research
                </Button>
              </Link>
              <Link to={user ? '/dashboard' : '/signup'} className="w-full sm:w-auto">
                <Button
                  variant="white"
                  size="lg"
                  className="w-full sm:w-auto px-8 finnova-btn-white justify-center text-sm sm:text-base"
                >
                  {user ? 'View Dashboard' : 'Create Free Account'}
                </Button>
              </Link>
            </div>

            {/* Trust Micro-Metrics */}
            <div className="flex flex-wrap items-center gap-4 sm:gap-6 pt-3 text-xs text-slate-500 font-medium">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-[#5b5dfa]" />
                <span>Deterministic Scoring</span>
              </div>
              <div className="flex items-center gap-2">
                <FileCheck2 className="h-4 w-4 text-emerald-500" />
                <span>Tier-1 Govt Sources</span>
              </div>
              <div className="flex items-center gap-2">
                <Scale className="h-4 w-4 text-amber-500" />
                <span>Explainable Uncertainty</span>
              </div>
            </div>
          </div>

          {/* Right Column (Interactive Intelligence Card): lg:col-span-5 */}
          <div className="lg:col-span-5 w-full">
            <div className="rounded-3xl bg-[#181534] p-5 sm:p-7 text-white shadow-2xl shadow-indigo-950/25 border border-slate-800 space-y-4">
              {/* Card Header */}
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="h-11 w-11 rounded-2xl bg-gradient-to-tr from-[#5b5dfa] to-[#7c3aed] flex items-center justify-center font-bold text-white text-base shadow-md shrink-0">
                    G
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm sm:text-base font-bold text-white truncate">Google LLC</p>
                      <span className="text-[10px] font-mono text-indigo-300 bg-indigo-500/20 px-2 py-0.5 rounded-full border border-indigo-400/20">
                        # RUN-894F2C
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5 truncate">
                      <Globe className="h-3 w-3 shrink-0 text-indigo-400" />
                      <span className="truncate">google.com • Mountain View, CA</span>
                    </p>
                  </div>
                </div>
                <StatusBadge status="verified" size="sm" />
              </div>

              {/* 3 Metric Grid inside card */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 sm:gap-3">
                <div className="rounded-2xl bg-[#232048] p-3 sm:p-3.5 border border-white/5 space-y-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Trust Index</span>
                  <p className="text-xl font-extrabold text-white">96.5%</p>
                  <p className="text-[10px] text-indigo-300 font-semibold truncate">High Confidence</p>
                </div>
                <div className="rounded-2xl bg-[#232048] p-3 sm:p-3.5 border border-white/5 space-y-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Evidence</span>
                  <p className="text-xl font-extrabold text-white">18 Items</p>
                  <p className="text-[10px] text-emerald-300 font-semibold truncate">Corroborated</p>
                </div>
                <div className="rounded-2xl bg-[#232048] p-3 sm:p-3.5 border border-white/5 space-y-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Risk Level</span>
                  <p className="text-xl font-extrabold text-emerald-400">0 Clean</p>
                  <p className="text-[10px] text-slate-400 font-semibold truncate">Domain Verified</p>
                </div>
              </div>

              {/* Evidence Snippet */}
              <div className="rounded-2xl bg-[#232048]/60 p-3.5 border border-white/5 text-xs text-slate-300 leading-relaxed space-y-1">
                <p className="font-bold text-white text-xs flex items-center gap-1.5">
                  <ShieldCheck className="h-3.5 w-3.5 text-[#818cf8]" />
                  <span>Public Registry Provenance</span>
                </p>
                <p className="text-[11px] text-slate-400">
                  Primary web domain verified through HTTPS TLS encryption. Active government registry records confirmed on SEC and MCA.
                </p>
              </div>

              {/* Card Footer */}
              <div className="pt-2 flex items-center justify-between border-t border-white/10 text-[11px] text-slate-400 font-mono">
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-400" />
                  <span>SHA-256 Verified</span>
                </div>
                <span className="text-indigo-300 font-sans font-semibold">Multi-Agent V1</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid: 4-Column Desktop / 2-Column Tablet / 1-Column Mobile */}
      <section className="mx-auto w-full max-w-[1440px] px-4 sm:px-6 lg:px-8 xl:px-10 py-10 sm:py-16">
        <div className="text-center space-y-2 sm:space-y-3 mb-8 sm:mb-12">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#181534]">
            Why Vishleshan AI?
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 font-medium max-w-xl mx-auto px-2">
            Engineered as an explainable, source-backed intelligence system for students, professionals, and placement cells.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          {features.map((f, i) => {
            const Icon = f.icon;
            return (
              <div
                key={i}
                className="rounded-2xl sm:rounded-3xl bg-white border border-slate-200/80 p-5 sm:p-6 shadow-sm hover:shadow-md transition-all space-y-3 min-w-0"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-50 text-[#5b5dfa] font-bold">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="text-sm sm:text-base font-bold text-[#181534]">{f.title}</h3>
                <p className="text-xs text-slate-500 font-medium leading-relaxed">{f.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Verification Hierarchy: 4-Column Desktop / 2-Column Tablet / 1-Column Mobile */}
      <section className="mx-auto w-full max-w-[1440px] px-4 sm:px-6 lg:px-8 xl:px-10 py-8 sm:py-12">
        <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 lg:p-10 shadow-sm space-y-6 sm:space-y-8">
          <div className="text-center space-y-2 max-w-2xl mx-auto">
            <h2 className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-[#181534]">
              Semantic Verification States
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 font-medium px-2">
              We communicate explicit uncertainty. Missing public records are never assumed to be fraud.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            {verificationStates.map((v, idx) => (
              <div key={idx} className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4 space-y-2 min-w-0">
                <StatusBadge status={v.status} size="sm" />
                <p className="text-xs text-slate-600 font-medium leading-relaxed pt-1">{v.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};
