import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowRight, ArrowLeft, RefreshCw, ExternalLink, AlertCircle } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

export const ForgotPassword: React.FC = () => {
  const { resetPassword } = useAuth();

  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState('');

  // Resend cooldown timer (30 seconds)
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    let timer: ReturnType<typeof setInterval>;
    if (cooldown > 0) {
      timer = setInterval(() => {
        setCooldown((prev) => prev - 1);
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [cooldown]);

  const validateEmail = (value: string): boolean => {
    const trimmed = value.trim();
    if (!trimmed) {
      setEmailError('Please enter your email address.');
      return false;
    }
    // Standard RFC-5322 compatible regex check
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(trimmed)) {
      setEmailError('Please enter a valid email address.');
      return false;
    }
    setEmailError(null);
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedEmail = email.trim();
    if (!validateEmail(trimmedEmail)) {
      return;
    }

    setIsLoading(true);
    const { error: resetError } = await resetPassword(trimmedEmail);
    setIsLoading(false);

    if (resetError) {
      // Show generic secure error without exposing internal tokens or errors
      setError("We couldn't complete the request. Please check your connection and try again.");
    } else {
      setSubmittedEmail(trimmedEmail);
      setIsSubmitted(true);
      setCooldown(30);
    }
  };

  const handleResend = async () => {
    if (cooldown > 0 || !submittedEmail || isLoading) return;

    setError(null);
    setIsLoading(true);
    const { error: resendError } = await resetPassword(submittedEmail);
    setIsLoading(false);

    if (resendError) {
      setError("We couldn't resend the reset email. Please try again.");
    } else {
      setCooldown(30);
    }
  };

  // ----------------------------------------------------
  // Confirmation State (Email Sent)
  // ----------------------------------------------------
  if (isSubmitted) {
    return (
      <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-200">
        <div className="text-center space-y-2">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 border border-indigo-100 text-[#5b5dfa] shadow-xs">
            <Mail className="h-7 w-7" />
          </div>
          <h2 className="text-xl font-bold tracking-tight text-[#181534]">
            Check your inbox
          </h2>
          <p className="text-xs text-slate-500 font-medium max-w-sm mx-auto leading-relaxed">
            We've sent a secure password reset link to:
          </p>
        </div>

        {/* Highlighted Email Badge */}
        <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 p-3.5 text-center">
          <span className="text-sm font-bold font-mono text-[#181534] break-all">
            {submittedEmail}
          </span>
        </div>

        <div className="rounded-2xl border border-indigo-100 bg-indigo-50/50 p-3.5 text-xs text-slate-600 leading-relaxed text-center font-medium">
          Check your email and follow the link to create a new password. The reset link is time-sensitive.
        </div>

        {error && (
          <div className="flex items-start gap-2.5 rounded-2xl border border-rose-200 bg-rose-50 p-3.5 text-xs font-semibold text-rose-700">
            <AlertCircle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
            <span className="leading-relaxed">{error}</span>
          </div>
        )}

        <div className="space-y-3 pt-1">
          <a
            href={`mailto:${submittedEmail}`}
            className="w-full inline-flex"
          >
            <Button
              type="button"
              variant="primary"
              className="w-full finnova-btn-primary py-3"
              rightIcon={<ExternalLink className="h-4 w-4" />}
            >
              Open Email App
            </Button>
          </a>

          <div className="text-center pt-2">
            {cooldown > 0 ? (
              <p className="text-xs font-medium text-slate-400">
                Didn't receive the email?{' '}
                <span className="font-semibold text-slate-500">
                  Resend available in {cooldown}s
                </span>
              </p>
            ) : (
              <button
                type="button"
                onClick={handleResend}
                disabled={isLoading}
                className="inline-flex items-center gap-1.5 text-xs font-bold text-[#5b5dfa] hover:underline disabled:opacity-50"
              >
                <RefreshCw className={`h-3 w-3 ${isLoading ? 'animate-spin' : ''}`} />
                <span>Didn't receive the email? Resend email</span>
              </button>
            )}
          </div>
        </div>

        <div className="pt-2 text-center text-xs text-slate-500 border-t border-slate-100">
          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 font-bold text-[#5b5dfa] hover:underline"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Sign In</span>
          </Link>
        </div>
      </div>
    );
  }

  // ----------------------------------------------------
  // Initial Form State
  // ----------------------------------------------------
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-200">
      <div className="space-y-1.5 text-center">
        <h2 className="text-xl font-bold tracking-tight text-[#181534]">
          Forgot your password?
        </h2>
        <p className="text-xs text-slate-500 font-medium leading-relaxed max-w-sm mx-auto">
          Don't worry. Enter the email associated with your Vishleshan AI account and we'll send you a secure password reset link.
        </p>
      </div>

      {error && (
        <div className="flex items-start gap-2.5 rounded-2xl border border-rose-200 bg-rose-50 p-3.5 text-xs font-semibold text-rose-700">
          <AlertCircle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
          <span className="leading-relaxed">{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <Input
          label="Email Address"
          type="email"
          placeholder="Enter your email address"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            if (emailError) validateEmail(e.target.value);
          }}
          leftIcon={<Mail className="h-4 w-4" />}
          error={emailError || undefined}
          required
          autoComplete="email"
          disabled={isLoading}
        />

        <Button
          type="submit"
          variant="primary"
          className="w-full finnova-btn-primary py-3"
          isLoading={isLoading}
          rightIcon={<ArrowRight className="h-4 w-4" />}
        >
          {isLoading ? 'Sending...' : 'Send Reset Link'}
        </Button>
      </form>

      <div className="pt-2 text-center text-xs text-slate-500 border-t border-slate-100">
        <Link
          to="/login"
          className="inline-flex items-center gap-1.5 font-bold text-[#5b5dfa] hover:underline"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Sign In</span>
        </Link>
      </div>
    </div>
  );
};
