import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Globe,
  Sparkles,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Clock,
  ShieldCheck,
} from 'lucide-react';
import { reportService } from '../services/reports';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

interface Step {
  id: number;
  label: string;
  desc: string;
}

const DEMO_STEPS: Step[] = [
  { id: 1, label: '1. Resolving company', desc: 'Querying public entity registers and identifying corporate presence' },
  { id: 2, label: '2. Analyzing company information', desc: 'Extracting executive overview, business model, and corporate hierarchy' },
  { id: 3, label: '3. Analyzing technology & reputation', desc: 'Evaluating digital presence, tech stack focus, and public sentiment' },
  { id: 4, label: '4. Analyzing recruitment signals', desc: 'Screening career portals, job channels, and scam vulnerability risks' },
  { id: 5, label: '5. Generating intelligence report', desc: 'Synthesizing evidence claims and formatting structured intelligence' },
];

const SUGGESTED_COMPANIES = [
  { name: 'HackIndia', url: 'https://hackindia.xyz' },
  { name: 'HCLTech', url: 'https://hcltech.com' },
  { name: 'Hindustan Aeronautics Limited', url: 'https://hal-india.co.in' },
  { name: 'Google', url: 'https://google.com' },
  { name: 'Microsoft', url: 'https://microsoft.com' },
  { name: 'TCS', url: 'https://tcs.com' },
  { name: 'Infosys', url: 'https://infosys.com' },
];

export const PresentationDemo: React.FC = () => {
  const navigate = useNavigate();

  const [companyName, setCompanyName] = useState('');
  const [officialUrl, setOfficialUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Animate progress steps during generation
  useEffect(() => {
    if (!isLoading) {
      setCurrentStepIndex(0);
      return;
    }

    const interval = setInterval(() => {
      setCurrentStepIndex((prev) => {
        if (prev < DEMO_STEPS.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 2800);

    return () => clearInterval(interval);
  }, [isLoading]);

  const handleAnalyze = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setError(null);

    const trimmed = companyName.trim();
    if (!trimmed) {
      setError('Please enter a company name.');
      return;
    }

    setIsLoading(true);
    setCurrentStepIndex(0);

    try {
      const response = await reportService.generateDemoCompanyReport(
        trimmed,
        officialUrl.trim() || undefined
      );

      if (response && response.report) {
        // Complete all steps visually
        setCurrentStepIndex(DEMO_STEPS.length);
        // Short pause to show completed steps, then open Report page
        setTimeout(() => {
          navigate(`/reports/${response.report.id}`, {
            state: {
              report: response.report,
              demoMode: true,
              sourceStatus: response.source_status,
            },
          });
        }, 600);
      } else {
        throw new Error('AI report generation failed. Please retry.');
      }
    } catch (err: unknown) {
      console.error('Presentation demo failure:', err);
      let errorMsg = 'AI report generation failed. Please retry.';
      if (err instanceof Error) {
        if (err.message.includes('503') || err.message.toLowerCase().includes('configured')) {
          errorMsg = 'Gemini API key is not configured in backend environment. Please verify Render environment variables.';
        } else if (err.message.includes('502') || err.message.toLowerCase().includes('temporarily')) {
          errorMsg = 'Gemini API temporarily unavailable. Please retry.';
        } else if (err.message) {
          errorMsg = err.message;
        }
      }
      setError(errorMsg);
      setIsLoading(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-4xl space-y-6 sm:space-y-8 animate-fade-in text-[#181534] pb-16">
      {/* Presentation Mode Hero Banner */}
      <div className="rounded-2xl sm:rounded-[32px] bg-gradient-to-br from-[#181534] via-[#232048] to-[#121028] p-6 sm:p-10 text-white shadow-xl border border-slate-800 text-center space-y-4">
        <div className="inline-flex items-center gap-2 rounded-full bg-[#5b5dfa]/20 border border-[#5b5dfa]/40 px-4 py-1 text-xs font-black tracking-wider text-indigo-300 uppercase">
          <Sparkles className="h-3.5 w-3.5 text-indigo-400 animate-pulse" />
          <span>VISHLESHAN AI PRESENTATION MODE</span>
        </div>

        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight text-white">
          Company Intelligence
        </h1>

        <p className="text-xs sm:text-sm font-medium text-slate-300 max-w-xl mx-auto leading-relaxed">
          Live Gemini company intelligence engine. Enter any domestic enterprise, MNC, or startup
          for real-time structured analysis, domain cross-referencing, and forensic risk evaluation.
        </p>

        {/* Live Gemini Honest Disclosure */}
        <div className="inline-flex items-center gap-2 text-xs font-mono text-indigo-200/80 bg-white/5 border border-white/10 rounded-full px-4 py-1">
          <ShieldCheck className="h-3.5 w-3.5 text-indigo-400" />
          <span>Real-time Gemini API • Zero hardcoded company fallbacks</span>
        </div>
      </div>

      {/* Input Form Card */}
      {!isLoading ? (
        <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-6 sm:p-10 shadow-sm space-y-6">
          {error && (
            <div className="flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs font-semibold text-rose-700">
              <AlertCircle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className="font-bold">{error}</p>
                <p className="text-slate-500 font-normal">
                  No fallback to other companies is allowed. Please check your inputs and try again.
                </p>
              </div>
            </div>
          )}

          <form onSubmit={handleAnalyze} className="space-y-5">
            <div className="space-y-1.5">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Company Name *
              </label>
              <Input
                type="text"
                placeholder="Enter company name (e.g. HackIndia, HCLTech, HAL, Google, TCS)"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                leftIcon={<Building2 className="h-4 w-4" />}
                required
                className="text-base py-3"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Optional Official Website
              </label>
              <Input
                type="text"
                placeholder="https://example.com"
                value={officialUrl}
                onChange={(e) => setOfficialUrl(e.target.value)}
                leftIcon={<Globe className="h-4 w-4" />}
                className="text-sm py-2.5 font-mono"
              />
            </div>

            <div className="pt-2">
              <Button
                type="submit"
                variant="primary"
                size="lg"
                className="w-full justify-center py-4 text-base font-bold shadow-lg shadow-indigo-500/25 bg-[#5b5dfa] hover:bg-[#4b4ce6]"
              >
                <span>ANALYZE COMPANY</span>
                <ArrowRight className="h-5 w-5 ml-1" />
              </Button>
            </div>
          </form>

          {/* Quick-Pick Presentation Shortcuts */}
          <div className="pt-4 border-t border-slate-100 space-y-2.5">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Quick Test Examples for Presentation:
            </span>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_COMPANIES.map((item) => (
                <button
                  key={item.name}
                  type="button"
                  onClick={() => {
                    setCompanyName(item.name);
                    setOfficialUrl(item.url);
                  }}
                  className="px-3 py-1.5 rounded-full text-xs font-bold bg-slate-100 hover:bg-indigo-50 hover:text-[#5b5dfa] text-slate-700 transition-all border border-slate-200/80 hover:border-indigo-300"
                >
                  {item.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* Progress Stepper View */
        <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-6 sm:p-10 shadow-sm space-y-8 animate-fade-in">
          <div className="text-center space-y-2">
            <div className="inline-flex items-center gap-2 text-xs font-bold text-[#5b5dfa] bg-indigo-50 border border-indigo-200/80 rounded-full px-3 py-1">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              <span>Live Analysis in Progress</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-[#181534]">
              Analyzing {companyName}
            </h2>
            <p className="text-xs text-slate-500 font-medium">
              Backend is streaming intelligence from Gemini API and structuring evidence.
            </p>
          </div>

          {/* Stepper Display */}
          <div className="space-y-4 max-w-lg mx-auto">
            {DEMO_STEPS.map((step, idx) => {
              const isCompleted = idx < currentStepIndex;
              const isCurrent = idx === currentStepIndex;

              return (
                <div
                  key={step.id}
                  className={`flex items-start gap-4 p-4 rounded-2xl border transition-all ${
                    isCurrent
                      ? 'bg-indigo-50/70 border-indigo-300 shadow-sm'
                      : isCompleted
                      ? 'bg-emerald-50/60 border-emerald-200'
                      : 'bg-slate-50/60 border-slate-200/60 opacity-60'
                  }`}
                >
                  <div className="shrink-0 mt-0.5">
                    {isCompleted ? (
                      <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                    ) : isCurrent ? (
                      <Loader2 className="h-5 w-5 text-[#5b5dfa] animate-spin" />
                    ) : (
                      <Clock className="h-5 w-5 text-slate-400" />
                    )}
                  </div>
                  <div className="min-w-0">
                    <p
                      className={`text-xs sm:text-sm font-bold ${
                        isCurrent
                          ? 'text-[#5b5dfa]'
                          : isCompleted
                          ? 'text-emerald-800'
                          : 'text-slate-600'
                      }`}
                    >
                      {step.label}
                    </p>
                    <p className="text-[11px] text-slate-500 font-medium mt-0.5 leading-relaxed">
                      {step.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="text-center pt-2">
            <span className="text-xs font-mono text-slate-400">
              Target endpoint: POST /api/v1/demo/company-report
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
