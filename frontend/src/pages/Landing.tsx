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
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/StatusBadge';
import { Logo } from '../components/ui/Logo';
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
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[800px] rounded-full bg-[#5b5dfa]/5 blur-[120px]" />
        <div className="absolute top-3/4 left-1/3 -translate-x-1/2 -translate-y-1/2 h-[400px] w-[600px] rounded-full bg-[#7c3aed]/5 blur-[140px]" />
      </div>

      {/* Hero Section */}
      <section className="relative mx-auto flex min-h-[80vh] max-w-6xl flex-col items-center justify-center px-4 sm:px-6 pt-12 pb-20 text-center">
        {/* Brand Ribbon Emblem */}
        <div className="mb-6">
          <Logo size="xl" theme="light" />
        </div>

        <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200/80 bg-indigo-50 px-4 py-1.5 text-xs font-bold text-[#5b5dfa] shadow-xs animate-fade-in">
          <Sparkles className="h-3.5 w-3.5" />
          <span>AI-Powered Company Intelligence & Verification Platform</span>
        </div>

        <h1 className="mt-6 text-4xl font-black tracking-tight sm:text-6xl md:text-7xl text-[#181534]">
          Verify Organizations with <br />
          <span className="bg-gradient-to-r from-[#5b5dfa] via-[#7c3aed] to-[#38bdf8] bg-clip-text text-transparent">
            Deterministic Evidence
          </span>
        </h1>

        <p className="mt-6 max-w-2xl text-base sm:text-lg leading-relaxed text-slate-500 font-medium">
          Research, verify and analyze companies using evidence-backed multi-agent intelligence,
          reproducible trust scoring, and recruitment risk forensics.
        </p>

        {/* CTA Buttons */}
        <div className="mt-10 flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto">
          <Link to={user ? '/research' : '/login'} className="w-full sm:w-auto">
            <Button
              variant="primary"
              size="lg"
              className="w-full sm:w-auto px-8 finnova-btn-primary"
              leftIcon={<Search className="h-5 w-5" />}
              rightIcon={<ArrowRight className="h-4 w-4" />}
            >
              Start Company Research
            </Button>
          </Link>
          <Link to={user ? '/dashboard' : '/register'} className="w-full sm:w-auto">
            <Button variant="white" size="lg" className="w-full sm:w-auto px-8 finnova-btn-white">
              {user ? 'View Dashboard' : 'Create Free Account'}
            </Button>
          </Link>
        </div>

        {/* Interactive Mini Preview (Finnova Style) */}
        <div className="mt-14 w-full max-w-4xl rounded-[32px] bg-[#181534] p-6 sm:p-8 text-white shadow-2xl border border-slate-800 text-left">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-[#5b5dfa] flex items-center justify-center font-bold text-white">
                G
              </div>
              <div>
                <p className="text-sm font-bold text-white">Google LLC</p>
                <p className="text-xs text-slate-400">google.com • Mountain View, CA</p>
              </div>
            </div>
            <StatusBadge status="verified" size="sm" />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
            <div className="rounded-2xl bg-[#232048] p-3 border border-white/5">
              <p className="text-[10px] font-bold text-slate-400 uppercase">Trust Index</p>
              <p className="text-xl font-extrabold text-white">96.5%</p>
            </div>
            <div className="rounded-2xl bg-[#232048] p-3 border border-white/5">
              <p className="text-[10px] font-bold text-slate-400 uppercase">Verified Evidence</p>
              <p className="text-xl font-extrabold text-white">9 Items</p>
            </div>
            <div className="rounded-2xl bg-[#232048] p-3 border border-white/5">
              <p className="text-[10px] font-bold text-slate-400 uppercase">Recruitment Risk</p>
              <p className="text-xl font-extrabold text-emerald-400">Low / Clean</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="mx-auto max-w-6xl px-4 sm:px-6 py-16">
        <div className="text-center space-y-3 mb-12">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#181534]">
            Why Vishleshan AI?
          </h2>
          <p className="text-sm text-slate-500 font-medium max-w-xl mx-auto">
            Engineered as an explainable, source-backed intelligence system for students, professionals, and placement cells.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((f, i) => {
            const Icon = f.icon;
            return (
              <div
                key={i}
                className="rounded-3xl bg-white border border-slate-200/80 p-6 shadow-sm hover:shadow-md transition-all space-y-3"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-50 text-[#5b5dfa] font-bold">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="text-base font-bold text-[#181534]">{f.title}</h3>
                <p className="text-xs text-slate-500 font-medium leading-relaxed">{f.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Verification Hierarchy (Finnova Rounded Cards) */}
      <section className="mx-auto max-w-6xl px-4 sm:px-6 py-12">
        <div className="rounded-[32px] bg-white border border-slate-200/80 p-8 sm:p-10 shadow-sm space-y-8">
          <div className="text-center space-y-2 max-w-2xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#181534]">
              Semantic Verification States
            </h2>
            <p className="text-xs text-slate-500 font-medium">
              We communicate explicit uncertainty. Missing public records are never assumed to be fraud.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {verificationStates.map((v, idx) => (
              <div key={idx} className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4 space-y-2">
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
