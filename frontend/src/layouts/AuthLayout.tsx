import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { Logo } from '../components/ui/Logo';

export const AuthLayout: React.FC = () => {
  return (
    <div className="relative min-h-screen flex flex-col justify-center items-center bg-[#f0f2f8] px-3.5 sm:px-4 py-8 sm:py-12 text-[#181534] selection:bg-[#5b5dfa]/20 selection:text-[#5b5dfa]">
      {/* Subtle ambient glow effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[500px] sm:w-[600px] h-[500px] sm:h-[600px] bg-[#5b5dfa]/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 left-1/2 -translate-x-1/2 w-[500px] sm:w-[600px] h-[500px] sm:h-[600px] bg-[#7c3aed]/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 w-full max-w-md space-y-4 sm:space-y-6">
        {/* Back Link */}
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-xs font-bold text-slate-500 hover:text-[#5b5dfa] transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Landing</span>
        </Link>

        {/* Brand Header with Logo */}
        <div className="text-center flex flex-col items-center justify-center space-y-2">
          <Link to="/">
            <Logo size="lg" theme="light" />
          </Link>
        </div>

        {/* Auth Container */}
        <div className="rounded-2xl sm:rounded-3xl bg-white border border-slate-200/80 p-5 sm:p-8 shadow-xl shadow-indigo-950/5">
          <Outlet />
        </div>

        {/* Footer Disclaimer */}
        <p className="text-center text-xs text-slate-400 leading-relaxed px-4">
          Evidence-driven corporate research. Secure sessions backed by Supabase Auth and Row Level Security.
        </p>
      </div>
    </div>
  );
};
