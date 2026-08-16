import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Loader2 } from 'lucide-react';

interface PublicOnlyRouteProps {
  children?: React.ReactNode;
}

export const PublicOnlyRoute: React.FC<PublicOnlyRouteProps> = ({ children }) => {
  const { user, loading, initialized } = useAuth();

  if (!initialized || loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f0f2f8] text-[#181534]">
        <div className="flex flex-col items-center gap-4 text-center rounded-3xl bg-white border border-slate-200/80 p-8 shadow-xl shadow-indigo-950/5 max-w-xs mx-4">
          <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-[#5b5dfa]">
            <Loader2 className="h-7 w-7 animate-spin text-[#5b5dfa]" />
          </div>
          <div>
            <p className="text-sm font-bold text-[#181534]">Loading Vishleshan AI...</p>
          </div>
        </div>
      </div>
    );
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return children ? <>{children}</> : <Outlet />;
};
