import React from 'react';
import { ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Logo } from '../ui/Logo';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-auto border-t border-slate-200/80 bg-white text-slate-500 py-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Platform Info */}
          <div className="md:col-span-2 space-y-3.5">
            <Logo size="md" theme="light" />
            <p className="text-xs text-slate-500 max-w-md leading-relaxed">
              AI-Powered Company Intelligence, Verification & Trust Analysis Platform.
              Evidence-driven, source-backed, explainable, and reproducible corporate intelligence.
            </p>
            <div className="rounded-2xl border border-indigo-100 bg-indigo-50/50 p-3.5 text-xs text-indigo-900/80 leading-relaxed max-w-md">
              <span className="font-bold text-[#5b5dfa]">Core Principle:</span> Vishleshan AI
              communicates uncertainty. Missing public evidence must not automatically be
              interpreted as fraud.
            </div>
          </div>

          {/* Navigation Links */}
          <div className="space-y-3">
            <p className="text-xs font-bold uppercase tracking-wider text-[#181534]">
              Platform
            </p>
            <ul className="space-y-2 text-xs font-semibold">
              <li>
                <Link to="/dashboard" className="hover:text-[#5b5dfa] transition-colors">
                  Overview
                </Link>
              </li>
              <li>
                <Link to="/research" className="hover:text-[#5b5dfa] transition-colors">
                  Company Research
                </Link>
              </li>
              <li>
                <Link to="/history" className="hover:text-[#5b5dfa] transition-colors">
                  Research History
                </Link>
              </li>
              <li>
                <Link to="/ask" className="hover:text-[#5b5dfa] transition-colors">
                  Ask AI Grounded Q&A
                </Link>
              </li>
            </ul>
          </div>

          {/* Verification Hierarchy */}
          <div className="space-y-3">
            <p className="text-xs font-bold uppercase tracking-wider text-[#181534]">
              Source Hierarchy
            </p>
            <ul className="space-y-2 text-xs text-slate-500 font-medium">
              <li className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                <span>Tier 1: Government & Regulators</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-[#5b5dfa]" />
                <span>Tier 2: Official Corporate Sites</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-blue-500" />
                <span>Tier 3: Reputable News Media</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-amber-500" />
                <span>Tier 4: Professional Platforms</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-10 pt-6 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <p>© {new Date().getFullYear()} Vishleshan AI. Production-Grade Engineering Platform.</p>
          <div className="flex items-center gap-4 font-semibold text-[#5b5dfa]">
            <span className="inline-flex items-center gap-1">
              Evidence-First Architecture
              <ExternalLink className="h-3 w-3" />
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};
