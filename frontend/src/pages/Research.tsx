import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Globe,
  Building2,
  Sparkles,
  ShieldCheck,
  AlertCircle,
  ArrowRight,
  Info,
  CheckCircle2,
} from 'lucide-react';
import { researchService } from '../services/research';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

export const Research: React.FC = () => {
  const navigate = useNavigate();

  const [companyName, setCompanyName] = useState('');
  const [companyUrl, setCompanyUrl] = useState('');
  const [deepVerification, setDeepVerification] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedName = companyName.trim();
    if (!trimmedName) {
      setError('Please enter a valid company or organization name');
      return;
    }

    let trimmedUrl = companyUrl.trim();
    if (trimmedUrl) {
      if (!/^https?:\/\//i.test(trimmedUrl)) {
        trimmedUrl = `https://${trimmedUrl}`;
      }
      try {
        new URL(trimmedUrl);
      } catch {
        setError('Please enter a valid official website URL');
        return;
      }
    }

    setIsLoading(true);
    try {
      const response = await researchService.startResearch({
        company_name: trimmedName,
        company_url: trimmedUrl || undefined,
        deep_verification: deepVerification,
      });

      navigate(`/research/${response.research_run_id}`);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Failed to start company research. Please check connection.';
      setError(msg);
      setIsLoading(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6 sm:space-y-8 animate-fade-in text-[#181534] pb-12">
      {/* Header */}
      <div className="space-y-2 text-left">
        <div className="inline-flex items-center gap-2 rounded-full bg-indigo-50 border border-indigo-200/80 px-3.5 py-1 text-xs font-bold text-[#5b5dfa]">
          <Sparkles className="h-3.5 w-3.5" />
          <span>New Evidence Research Run</span>
        </div>
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-[#181534]">
          Initiate Company Research
        </h1>
        <p className="text-xs sm:text-sm font-medium text-slate-500 max-w-2xl leading-relaxed">
          Launch multi-agent forensic verification across government registers, official domains,
          news archives, and recruitment signals.
        </p>
      </div>

      {/* Main Form Card (2-Column Grid on Desktop / 1-Column on Mobile) */}
      <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 shadow-sm space-y-6">
        <div className="border-b border-slate-100 pb-4 sm:pb-5">
          <h2 className="text-lg sm:text-xl font-bold text-[#181534] flex items-center gap-2.5">
            <Building2 className="h-5 w-5 text-[#5b5dfa]" />
            <span>Target Organization Details</span>
          </h2>
          <p className="mt-1 text-xs text-slate-500 font-medium">
            Provide the company name and optional official domain to initiate automated multi-agent research.
          </p>
        </div>

        {error && (
          <div className="flex items-start gap-2.5 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs font-semibold text-rose-700">
            <AlertCircle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
            <span className="leading-relaxed">{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 2-Column Responsive Input Grid on Tablet & Desktop */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <Input
              label="Company Name *"
              type="text"
              placeholder="e.g. Google, Infosys, OpenAI"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              leftIcon={<Building2 className="h-4 w-4" />}
              helperText="Official legal or trading name of the company to investigate."
              required
              disabled={isLoading}
            />

            <Input
              label="Official Website URL (Optional)"
              type="text"
              placeholder="e.g. google.com or https://openai.com"
              value={companyUrl}
              onChange={(e) => setCompanyUrl(e.target.value)}
              leftIcon={<Globe className="h-4 w-4" />}
              helperText="Supplying an official domain accelerates domain provenance verification."
              disabled={isLoading}
            />
          </div>

          {/* Verification depth toggle */}
          <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4 space-y-2">
            <label className="flex items-start sm:items-center gap-3.5 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={deepVerification}
                onChange={(e) => setDeepVerification(e.target.checked)}
                className="mt-1 sm:mt-0 h-4 w-4 rounded border-slate-300 text-[#5b5dfa] focus:ring-[#5b5dfa]"
                disabled={isLoading}
              />
              <div>
                <span className="text-sm font-bold text-[#181534]">
                  Enable Full 8-Agent Deep Intelligence Pipeline
                </span>
                <p className="text-xs text-slate-500 font-medium leading-relaxed">
                  Includes company identity resolution, registration cross-referencing, news/hiring signals, and recruitment risk forensics.
                </p>
              </div>
            </label>
          </div>

          <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 border-t border-slate-100">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 justify-center sm:justify-start">
              <ShieldCheck className="h-4 w-4 text-[#5b5dfa]" />
              <span>Deterministic Multi-Agent fusion & trust scoring</span>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full sm:w-auto px-8 finnova-btn-primary justify-center"
              isLoading={isLoading}
              leftIcon={<Search className="h-4 w-4" />}
              rightIcon={<ArrowRight className="h-4 w-4" />}
            >
              Start Research
            </Button>
          </div>
        </form>
      </div>

      {/* Informational Guidance (Desktop 3 cols, Tablet 2 cols, Mobile 1 col) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        <div className="rounded-2xl sm:rounded-3xl border border-slate-200/80 bg-white p-5 space-y-2 shadow-xs min-w-0">
          <div className="flex items-center gap-2 text-xs font-bold text-[#181534]">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            <span>Tier-1 Sources</span>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed font-medium">
            Directly cross-checks government registries (MCA, SEC, Companies House) where publicly accessible.
          </p>
        </div>

        <div className="rounded-2xl sm:rounded-3xl border border-slate-200/80 bg-white p-5 space-y-2 shadow-xs min-w-0">
          <div className="flex items-center gap-2 text-xs font-bold text-[#181534]">
            <ShieldCheck className="h-4 w-4 text-[#5b5dfa]" />
            <span>Recruitment Risk</span>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed font-medium">
            Examines career portal legitimacy, domain spoofing risks, and anomalous recruitment practices.
          </p>
        </div>

        <div className="rounded-2xl sm:rounded-3xl border border-slate-200/80 bg-white p-5 space-y-2 shadow-xs sm:col-span-2 lg:col-span-1 min-w-0">
          <div className="flex items-center gap-2 text-xs font-bold text-[#181534]">
            <Info className="h-4 w-4 text-amber-500" />
            <span>Uncertainty First</span>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed font-medium">
            Missing public information is communicated explicitly and never defaulted to fraud.
          </p>
        </div>
      </div>
    </div>
  );
};
