import React, { useState } from 'react';
import { NavLink, Link, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Search,
  History,
  MessageSquareText,
  LogOut,
  User as UserIcon,
  Menu,
  X,
  ChevronDown,
  Sparkles,
  Bell,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { Logo } from '../ui/Logo';
import { Button } from '../ui/Button';

export const Navbar: React.FC = () => {
  const { user, profile, signOut } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);

  const handleSignOut = async () => {
    await signOut();
    navigate('/login');
  };

  const navItems = [
    { label: 'Overview', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Research', path: '/research', icon: Search },
    { label: 'History', path: '/history', icon: History },
    { label: 'Ask AI', path: '/ask', icon: MessageSquareText },
  ];

  return (
    <header className="sticky top-0 z-40 w-full bg-[#f0f2f8]/95 backdrop-blur-xl border-b border-slate-200/80">
      <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand Logo with Custom Vishleshan AI Icon */}
        <Link to={user ? '/dashboard' : '/'} className="flex items-center gap-3 group">
          <Logo size="md" theme="light" />
        </Link>

        {/* Center Floating Dark Pill Navigation Bar (Finnova Style) */}
        {user && (
          <nav className="hidden md:inline-flex items-center gap-1 rounded-full bg-[#181534] px-2 py-1.5 shadow-lg shadow-indigo-950/10 border border-slate-800">
            {navItems.map((item) => {
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `rounded-full px-4 py-1.5 text-xs font-semibold tracking-wide transition-all ${
                      isActive
                        ? 'bg-[#5b5dfa] text-white shadow-md shadow-indigo-500/40'
                        : 'text-slate-400 hover:text-white hover:bg-white/5'
                    }`
                  }
                >
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        )}

        {/* Right Side Utility Actions & Profile (Finnova Style) */}
        <div className="hidden md:flex items-center gap-2.5">
          {user ? (
            <>
              {/* Utility Quick Icons */}
              <Link
                to="/research"
                title="Search / Research"
                className="flex h-9 w-9 items-center justify-center rounded-xl bg-white border border-slate-200/80 text-slate-600 hover:text-[#5b5dfa] hover:border-[#5b5dfa]/40 shadow-xs transition-all"
              >
                <Search className="h-4 w-4" />
              </Link>
              <div
                title="System Notifications"
                className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-white border border-slate-200/80 text-slate-600 hover:text-[#5b5dfa] shadow-xs cursor-pointer transition-all"
              >
                <Bell className="h-4 w-4" />
                <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-[#5b5dfa]" />
              </div>

              {/* User Profile Pill Dropdown */}
              <div className="relative ml-1">
                <button
                  type="button"
                  onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                  className="flex items-center gap-2.5 rounded-full bg-white border border-slate-200/80 pl-1.5 pr-3 py-1 shadow-xs hover:border-slate-300 transition-all focus:outline-none"
                >
                  <div className="relative flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-tr from-[#5b5dfa] to-[#7c3aed] text-white font-bold text-xs shadow-xs">
                    {profile?.full_name?.charAt(0).toUpperCase() ||
                      user.email?.charAt(0).toUpperCase() || (
                        <UserIcon className="h-3.5 w-3.5" />
                      )}
                    <span className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full bg-emerald-500 ring-2 ring-white" />
                  </div>
                  <div className="text-left min-w-0 max-w-[110px]">
                    <p className="truncate text-xs font-bold text-[#181534]">
                      {profile?.full_name || user.email?.split('@')[0]}
                    </p>
                  </div>
                  <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
                </button>

                {profileDropdownOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setProfileDropdownOpen(false)}
                    />
                    <div className="absolute right-0 mt-2 w-60 rounded-3xl border border-slate-200/80 bg-white p-3 shadow-2xl z-50 animate-in fade-in slide-in-from-top-2 duration-150 text-[#181534]">
                      <div className="p-2.5 border-b border-slate-100 mb-1.5">
                        <p className="text-xs font-bold text-[#181534] truncate">
                          {profile?.full_name || 'Vishleshan User'}
                        </p>
                        <p className="text-[11px] text-slate-500 truncate">
                          {user.email}
                        </p>
                        <span className="inline-block mt-1 text-[9px] font-extrabold uppercase tracking-wider bg-indigo-50 text-[#5b5dfa] px-2 py-0.5 rounded-full">
                          {profile?.role || 'User'}
                        </span>
                      </div>
                      <Link
                        to="/research"
                        onClick={() => setProfileDropdownOpen(false)}
                        className="flex items-center gap-2.5 rounded-2xl px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:text-[#5b5dfa] transition-colors"
                      >
                        <Sparkles className="h-3.5 w-3.5 text-[#5b5dfa]" />
                        <span>New Research Run</span>
                      </Link>
                      <button
                        type="button"
                        onClick={() => {
                          setProfileDropdownOpen(false);
                          handleSignOut();
                        }}
                        className="w-full flex items-center gap-2.5 rounded-2xl px-3 py-2 text-xs font-semibold text-rose-500 hover:bg-rose-50 transition-colors text-left"
                      >
                        <LogOut className="h-3.5 w-3.5" />
                        <span>Sign Out</span>
                      </button>
                    </div>
                  </>
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Link to="/login">
                <Button variant="ghost" size="sm" className="text-[#181534] font-semibold hover:bg-slate-200/60 rounded-full">
                  Sign In
                </Button>
              </Link>
              <Link to="/register">
                <Button variant="primary" size="sm" className="bg-[#5b5dfa] hover:bg-[#4f46e5] rounded-full text-white font-semibold shadow-md shadow-indigo-500/25">
                  Get Started
                </Button>
              </Link>
            </div>
          )}
        </div>

        {/* Mobile Hamburger */}
        <div className="flex md:hidden">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="flex h-10 w-10 items-center justify-center rounded-2xl border border-slate-200 bg-white text-slate-700 shadow-xs"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="border-b border-slate-200 bg-white px-4 pt-3 pb-6 md:hidden text-[#181534] shadow-xl">
          {user ? (
            <div className="space-y-3">
              <div className="flex items-center gap-3 p-3 rounded-2xl bg-slate-50 border border-slate-100">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#5b5dfa] text-white font-bold">
                  {profile?.full_name?.charAt(0).toUpperCase() ||
                    user.email?.charAt(0).toUpperCase() || (
                      <UserIcon className="h-4 w-4" />
                    )}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-sm font-bold text-[#181534]">
                    {profile?.full_name || user.email?.split('@')[0]}
                  </p>
                  <p className="truncate text-xs text-slate-500">{user.email}</p>
                </div>
              </div>

              <nav className="space-y-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className={({ isActive }) =>
                        `flex items-center gap-3 rounded-2xl px-4 py-2.5 text-sm font-semibold transition-all ${
                          isActive
                            ? 'bg-[#5b5dfa] text-white shadow-md'
                            : 'text-slate-600 hover:bg-slate-100'
                        }`
                      }
                    >
                      <Icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </NavLink>
                  );
                })}
              </nav>

              <button
                type="button"
                onClick={() => {
                  setMobileMenuOpen(false);
                  handleSignOut();
                }}
                className="w-full flex items-center justify-center gap-2 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm font-semibold text-rose-600"
              >
                <LogOut className="h-4 w-4" />
                <span>Sign Out</span>
              </button>
            </div>
          ) : (
            <div className="space-y-2 pt-2">
              <Link
                to="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="block w-full text-center rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                onClick={() => setMobileMenuOpen(false)}
                className="block w-full text-center rounded-2xl bg-[#5b5dfa] text-white px-4 py-2.5 text-sm font-semibold shadow-md"
              >
                Get Started
              </Link>
            </div>
          )}
        </div>
      )}
    </header>
  );
};
