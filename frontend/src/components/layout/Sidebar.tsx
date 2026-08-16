import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Search,
  History,
  MessageSquareText,
  ShieldCheck,
  Building2,
  FileCheck,
  AlertTriangle,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const links = [
    { label: 'Overview', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Research Company', path: '/research', icon: Search },
    { label: 'Research History', path: '/history', icon: History },
    { label: 'Ask AI Grounded', path: '/ask', icon: MessageSquareText },
  ];

  return (
    <aside className="w-64 shrink-0 hidden lg:block">
      <div className="sticky top-28 space-y-5">
        <div className="rounded-3xl border border-slate-200/80 bg-white p-4 shadow-sm">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-3 pb-2">
            Navigation
          </p>
          <nav className="space-y-1.5">
            {links.map((link) => {
              const Icon = link.icon;
              return (
                <NavLink
                  key={link.path}
                  to={link.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-2xl px-4 py-2.5 text-sm font-semibold transition-all ${
                      isActive
                        ? 'bg-[#5b5dfa] text-white shadow-md shadow-indigo-500/25'
                        : 'text-slate-600 hover:bg-slate-50 hover:text-[#181534]'
                    }`
                  }
                >
                  <Icon className="h-4 w-4" />
                  <span>{link.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Intelligence Principles Callout (Finnova Rounded Style) */}
        <div className="rounded-3xl border border-slate-200/80 bg-white p-5 text-xs text-slate-500 space-y-3.5 shadow-sm">
          <div className="flex items-center gap-2 text-[#181534] font-bold text-xs">
            <ShieldCheck className="h-4 w-4 text-[#5b5dfa]" />
            <span>Verification States</span>
          </div>
          <div className="space-y-2.5 text-xs font-semibold">
            <div className="flex items-center gap-2 text-emerald-600">
              <Building2 className="h-4 w-4 shrink-0" />
              <span>Verified Entity & Records</span>
            </div>
            <div className="flex items-center gap-2 text-amber-600">
              <FileCheck className="h-4 w-4 shrink-0" />
              <span>Unverified / Partial</span>
            </div>
            <div className="flex items-center gap-2 text-purple-600">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>Conflicting Signals</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-400 pt-2 border-t border-slate-100 leading-relaxed">
            Missing public evidence is strictly communicated as uncertainty and never defaulted to fraud.
          </p>
        </div>
      </div>
    </aside>
  );
};
