import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Loader2, AlertCircle, ArrowLeft, RefreshCw, CheckCircle2 } from 'lucide-react';
import { supabase } from '../lib/supabase';
import { Button } from '../components/ui/Button';

export const AuthCallback: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const processAuth = async () => {
      // 1. Check for error parameters in hash or search query
      const hash = window.location.hash;
      const search = location.search;

      const hashParams = new URLSearchParams(hash.replace(/^#/, ''));
      const queryParams = new URLSearchParams(search);

      // Check if this is a password recovery callback
      const authType = hashParams.get('type') || queryParams.get('type');
      if (authType === 'recovery') {
        navigate(`/reset-password${window.location.hash || location.search}`, { replace: true });
        return;
      }

      const error = hashParams.get('error') || queryParams.get('error');
      const errorDescription =
        hashParams.get('error_description') || queryParams.get('error_description');

      if (error) {
        if (!isMounted) return;
        setStatus('error');
        if (error === 'access_denied') {
          setErrorMessage('Google sign-in was cancelled.');
        } else {
          setErrorMessage(
            errorDescription
              ? decodeURIComponent(errorDescription.replace(/\+/g, ' '))
              : "We couldn't complete Google sign-in. Please try again."
          );
        }
        return;
      }

      // 2. Check for active session or exchange
      try {
        const {
          data: { session },
          error: sessionError,
        } = await supabase.auth.getSession();

        if (sessionError) {
          if (!isMounted) return;
          setStatus('error');
          setErrorMessage("We couldn't complete authentication. Please try again.");
          return;
        }

        if (session?.user) {
          // Sync profile if needed
          try {
            const fullName =
              session.user.user_metadata?.full_name ||
              session.user.user_metadata?.name ||
              session.user.email?.split('@')[0] ||
              'User';

            await supabase.from('profiles').upsert(
              {
                id: session.user.id,
                full_name: fullName,
                role: 'user',
              },
              { onConflict: 'id' }
            );
          } catch {
            // Profile sync fallback
          }

          if (!isMounted) return;
          setStatus('success');

          // Smooth redirect to dashboard
          setTimeout(() => {
            if (isMounted) {
              navigate('/dashboard', { replace: true });
            }
          }, 600);
          return;
        }

        // Listen for auth change if session is still processing
        const {
          data: { subscription },
        } = supabase.auth.onAuthStateChange(async (event, newSession) => {
          if (!isMounted) return;

          if (event === 'SIGNED_IN' && newSession?.user) {
            try {
              const fullName =
                newSession.user.user_metadata?.full_name ||
                newSession.user.user_metadata?.name ||
                newSession.user.email?.split('@')[0] ||
                'User';

              await supabase.from('profiles').upsert(
                {
                  id: newSession.user.id,
                  full_name: fullName,
                  role: 'user',
                },
                { onConflict: 'id' }
              );
            } catch {
              // Profile sync fallback
            }

            setStatus('success');
            setTimeout(() => {
              if (isMounted) {
                navigate('/dashboard', { replace: true });
              }
            }, 600);
          }
        });

        // 5-second timeout safeguard
        const timer = setTimeout(() => {
          if (isMounted && status === 'loading') {
            setStatus('error');
            setErrorMessage('Authentication timed out. Please try signing in again.');
          }
        }, 5000);

        return () => {
          subscription.unsubscribe();
          clearTimeout(timer);
        };
      } catch (err) {
        if (!isMounted) return;
        setStatus('error');
        setErrorMessage(
          err instanceof Error
            ? err.message
            : "Something went wrong. Please check your connection and try again."
        );
      }
    };

    processAuth();

    return () => {
      isMounted = false;
    };
  }, [location, navigate, status]);

  if (status === 'error') {
    return (
      <div className="space-y-6 text-center animate-in fade-in slide-in-from-bottom-2 duration-200">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-50 border border-rose-200 text-rose-600 shadow-xs">
          <AlertCircle className="h-7 w-7" />
        </div>

        <div className="space-y-1.5">
          <h2 className="text-xl font-bold tracking-tight text-[#181534]">
            Authentication Failed
          </h2>
          <p className="text-xs text-slate-500 font-medium leading-relaxed max-w-sm mx-auto">
            {errorMessage || "We couldn't complete the sign-in request. Please try again."}
          </p>
        </div>

        <div className="space-y-3 pt-2">
          <Link to="/login" className="w-full inline-flex">
            <Button
              type="button"
              variant="primary"
              className="w-full finnova-btn-primary py-3"
              leftIcon={<RefreshCw className="h-4 w-4" />}
            >
              Try Signing In Again
            </Button>
          </Link>

          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-[#5b5dfa] transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Sign In</span>
          </Link>
        </div>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="space-y-6 text-center animate-in fade-in duration-200">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-600 shadow-xs">
          <CheckCircle2 className="h-7 w-7" />
        </div>

        <div className="space-y-1.5">
          <h2 className="text-xl font-bold tracking-tight text-[#181534]">
            Authentication Successful
          </h2>
          <p className="text-xs text-slate-500 font-medium">
            Redirecting you to Vishleshan AI Dashboard...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 text-center py-4 animate-in fade-in duration-200">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 border border-indigo-100 text-[#5b5dfa] shadow-xs">
        <Loader2 className="h-7 w-7 animate-spin text-[#5b5dfa]" />
      </div>

      <div className="space-y-1.5">
        <h2 className="text-xl font-bold tracking-tight text-[#181534]">
          Verifying Credentials
        </h2>
        <p className="text-xs text-slate-500 font-medium">
          Connecting to Vishleshan AI secure provenance...
        </p>
      </div>
    </div>
  );
};
