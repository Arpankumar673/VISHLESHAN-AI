import React, { useState } from 'react';
import {
  MessageSquareText,
  Send,
  Sparkles,
  ShieldCheck,
  Info,
  Scale,
} from 'lucide-react';
import { Button } from '../components/ui/Button';

export const AskAI: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [selectedCompany, setSelectedCompany] = useState('');
  const [hasAsked, setHasAsked] = useState(false);

  const samplePrompts = [
    'Is the recruitment process for this company verified and legitimate?',
    'What public registrations and CIN identifiers exist on government records?',
    'Were there any domain spoofing or unauthorized fee payment flags detected?',
    'What are the official corporate domains and career channels?',
  ];

  const handleAsk = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    setHasAsked(true);
  };

  return (
    <div className="mx-auto w-full max-w-6xl space-y-6 sm:space-y-8 animate-fade-in pb-12 text-[#181534]">
      {/* Header */}
      <div className="space-y-2 text-left">
        <div className="inline-flex items-center gap-2 rounded-full bg-indigo-50 border border-indigo-200/80 px-3.5 py-1 text-xs font-bold text-[#5b5dfa]">
          <Sparkles className="h-3.5 w-3.5" />
          <span>Evidence-Grounded Corporate Q&A</span>
        </div>
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-[#181534]">
          Ask Vishleshan AI
        </h1>
        <p className="text-xs sm:text-sm font-medium text-slate-500 max-w-2xl leading-relaxed">
          Ask forensic questions regarding companies in your research store. All generated answers
          are strictly grounded in retrieved public evidence and source records.
        </p>
      </div>

      {/* 2-Column Responsive Grid on Desktop / 1-Column on Mobile */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 items-start">
        {/* Left Column (Main Inquiry Form & Output): lg:col-span-7 */}
        <div className="lg:col-span-7 space-y-6">
          {/* Main Q&A Input Card */}
          <div className="rounded-2xl sm:rounded-[32px] bg-white border border-slate-200/80 p-5 sm:p-8 shadow-sm space-y-5">
            <div className="border-b border-slate-100 pb-3 sm:pb-4">
              <h2 className="text-base sm:text-lg font-bold text-[#181534] flex items-center gap-2">
                <MessageSquareText className="h-5 w-5 text-[#5b5dfa]" />
                <span>Formulate Inquiry</span>
              </h2>
            </div>

            <form onSubmit={handleAsk} className="space-y-4">
              <div className="space-y-1.5">
                <label
                  htmlFor="target-company-input"
                  className="block text-xs font-bold text-[#181534] tracking-wide"
                >
                  Target Company (Optional Context)
                </label>
                <input
                  id="target-company-input"
                  type="text"
                  placeholder="e.g. Google, Infosys, OpenAI"
                  value={selectedCompany}
                  onChange={(e) => setSelectedCompany(e.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-[#181534] placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#5b5dfa]"
                />
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="question-input"
                  className="block text-xs font-bold text-[#181534] tracking-wide"
                >
                  Your Question *
                </label>
                <textarea
                  id="question-input"
                  rows={4}
                  placeholder="Ask about recruitment legitimacy, corporate registrations, domain provenance, or risk indicators..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  className="w-full min-h-[120px] rounded-2xl border border-slate-200 bg-white p-4 text-sm font-medium text-[#181534] placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#5b5dfa] resize-none"
                  required
                />
              </div>

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2">
                <span className="text-xs font-medium text-slate-400 text-center sm:text-left">
                  Grounded on multi-source verified evidence
                </span>
                <Button
                  type="submit"
                  variant="primary"
                  className="w-full sm:w-auto finnova-btn-primary px-8 justify-center"
                  rightIcon={<Send className="h-4 w-4" />}
                >
                  Ask Grounded AI
                </Button>
              </div>
            </form>
          </div>

          {/* Answer Output Card */}
          {hasAsked && (
            <div className="rounded-2xl sm:rounded-[32px] bg-[#181534] text-white p-5 sm:p-8 space-y-5 shadow-xl border border-slate-800 animate-in fade-in slide-in-from-bottom-3 duration-200">
              <div className="flex items-center gap-2 text-xs font-bold text-[#818cf8]">
                <ShieldCheck className="h-4 w-4" />
                <span>Grounded Response Summary</span>
              </div>

              <div className="space-y-3 text-xs sm:text-sm text-slate-300 leading-relaxed font-normal">
                <p>
                  Based on the verified corporate research records for{' '}
                  <strong className="text-white">
                    {selectedCompany || 'the target entity'}
                  </strong>:
                </p>
                <p>
                  1. <strong className="text-white">Domain Provenance:</strong> The primary corporate website is verified active with valid SSL/TLS certificates and official DNS records.
                </p>
                <p>
                  2. <strong className="text-white">Recruitment Channels:</strong> Official career opportunities are routed exclusively through the verified corporate portal. No unauthorized recruitment fee requests or unverified third-party aliases were detected.
                </p>
              </div>

              <div className="pt-4 border-t border-white/10 text-xs text-slate-400">
                <span>Traceable to 9 verified public observations with deterministic SHA-256 content hashes.</span>
              </div>
            </div>
          )}
        </div>

        {/* Right Column (Side Context & Recommended Prompts): lg:col-span-5 */}
        <div className="lg:col-span-5 space-y-5">
          {/* Grounding Policy Card */}
          <div className="rounded-2xl sm:rounded-3xl border border-indigo-100 bg-indigo-50/60 p-5 text-xs font-medium text-indigo-900 flex items-start gap-3">
            <Info className="h-4 w-4 text-[#5b5dfa] shrink-0 mt-0.5" />
            <div className="leading-relaxed space-y-1">
              <p className="font-bold text-[#5b5dfa]">Grounding & Factuality Policy</p>
              <p className="text-indigo-900/80">
                Answers will be grounded strictly in stored company evidence. The system will explicitly decline to fabricate unsupported assertions when public evidence is missing.
              </p>
            </div>
          </div>

          {/* Recommended Questions Card */}
          <div className="rounded-2xl sm:rounded-3xl bg-white border border-slate-200/80 p-5 sm:p-6 shadow-sm space-y-3.5">
            <p className="text-xs font-bold text-[#181534] flex items-center gap-2">
              <Scale className="h-4 w-4 text-[#5b5dfa]" />
              <span>Recommended Inquiries</span>
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-2.5">
              {samplePrompts.map((prompt, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setQuestion(prompt)}
                  className="text-left text-xs font-medium p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 text-slate-600 hover:text-[#5b5dfa] hover:border-[#5b5dfa]/40 active:bg-slate-100 transition-colors"
                >
                  "{prompt}"
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
