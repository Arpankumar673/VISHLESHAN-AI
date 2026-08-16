import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  Lock,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  ShieldCheck,
  RotateCcw,
} from 'lucide-react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

type PasswordStrength = 'weak' | 'fair' | 'good' | 'strong';

export const ResetPassword: React.FC = () => {
  const { updatePassword } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [confirmError, setConfirmError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [isInvalidLink, setIsInvalidLink] = useState(false);
  const [isCheckingLink, setIsCheckingLink] = useState(true);

  // Check URL hash and session state on mount
  useEffect(() => {
    const checkRecoverySession = async () => {
      // Check for error parameters in URL hash (e.g. #error=access_denied&error_code=otp_expired)
      const hash = window.location.hash;
      if (hash) {
        const params = new URLSearchParams(hash.replace(/^#/, ''));
        const error = params.get('error');
        const errorCode = params.get('error_code');
        if (error || errorCode) {
          setIsInvalidLink(true);
          setIsCheckingLink(false);
          return;
        }
      }

      // Check query params if any
      const searchParams = new URLSearchParams(location.search);
      if (searchParams.get('error') || searchParams.get('error_code')) {
        setIsInvalidLink(true);
        setIsCheckingLink(false);
        return;
      }

      // Check if active Supabase session or recovery event exists
      try {
        const { data: { session } } = await supabase.auth.getSession();
        // If there is no session and no hash access token, the user navigated directly to /reset-password
        if (!session && !hash.includes('access_token')) {
          setIsInvalidLink(true);
        }
      } catch {
        setIsInvalidLink(true);
      } finally {
        setIsCheckingLink(false);
      }
    };

    checkRecoverySession();
  }, [location]);

  // Compute password strength
  const calculateStrength = (pass: string): { level: PasswordStrength; score: number; label: string; color: string } => {
    if (!pass) return { level: 'weak', score: 0, label: 'Empty', color: 'bg-slate-200' };

    let score = 0;
    if (pass.length >= 6) score += 1;
    if (pass.length >= 10) score += 1;
    if (/[A-Z]/.test(pass) && /[a-z]/.test(pass)) score += 1;
    if (/[0-9]/.test(pass)) score += 1;
    if (/[^A-Za-z0-9]/.test(pass)) score += 1;

    if (score <= 1) {
      return { level: 'weak', score: 25, label: 'Weak', color: 'bg-rose-500' };
    }
    if (score === 2) {
      return { level: 'fair', score: 50, label: 'Fair', color: 'bg-amber-500' };
    }
    if (score === 3 || score === 4) {
      return { level: 'good', score: 75, label: 'Good', color: 'bg-[#5b5dfa]' };
    }
    return { level: 'strong', score: 100, label: 'Strong', color: 'bg-emerald-500' };
  };

  const strength = calculateStrength(password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setPasswordError(null);
    setConfirmError(null);

    // Validate password length
    if (!password) {
      setPasswordError('Please enter a new password.');
      return;
    }
    if (password.length < 6) {
      setPasswordError('Password must be at least 6 characters.');
      return;
    }

    // Validate confirmation match
    if (!confirmPassword) {
      setConfirmError('Please confirm your new password.');
      return;
    }
    if (password !== confirmPassword) {
      setConfirmError('Passwords do not match.');
      return;
    }

    setIsLoading(true);
    const { error: updateErr } = await updatePassword(password);
    setIsLoading(false);

    if (updateErr) {
      setFormError("We couldn't update your password. Please try again or request a new reset link.");
    } else {
      setIsSuccess(true);
    }
  };

  // ----------------------------------------------------
  // Initial Checking Link Loading State
  // ----------------------------------------------------
  if (isCheckingLink) {
    return (
      <div className="py-8 text-center space-y-3">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-[#5b5dfa] animate-pulse">
          <ShieldCheck className="h-6 w-6" />
        </div>
        <p className="text-xs font-semibold text-slate-500">
          Verifying security recovery link...
        </p>
      </div>
    );
  }

  // ----------------------------------------------------
  // Invalid or Expired Link State
  // ----------------------------------------------------
  if (isInvalidLink) {
    return (
      <div className="space-y-6 text-center animate-in fade-in slide-in-from-bottom-2 duration-200">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-50 border border-amber-200 text-amber-600 shadow-xs">
          <AlertTriangle className="h-7 w-7" />
        </div>

        <div className="space-y-1.5">
          <h2 className="text-xl font-bold tracking-tight text-[#181534]">
            Link Invalid or Expired
          </h2>
          <p className="text-xs text-slate-500 font-medium leading-relaxed max-w-sm mx-auto">
            This password reset link is invalid or has expired. For your security, reset links can only be used once and expire shortly after delivery.
          </p>
        </div>

        <div className="space-y-3 pt-2">
          <Link to="/forgot-password" className="w-full inline-flex">
            <Button
              type="button"
              variant="primary"
              className="w-full finnova-btn-primary py-3"
              leftIcon={<RotateCcw className="h-4 w-4" />}
            >
              Request New Reset Link
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

  // ----------------------------------------------------
  // Success State (Password Updated)
  // ----------------------------------------------------
  if (isSuccess) {
    return (
      <div className="space-y-6 text-center animate-in fade-in slide-in-from-bottom-2 duration-200">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-600 shadow-xs">
          <CheckCircle2 className="h-7 w-7" />
        </div>

        <div className="space-y-1.5">
          <h2 className="text-xl font-bold tracking-tight text-[#181534]">
            Password updated successfully
          </h2>
          <p className="text-xs text-slate-500 font-medium leading-relaxed max-w-sm mx-auto">
            Your Vishleshan AI password has been changed. You can now sign in using your new credentials.
          </p>
        </div>

        <div className="pt-2">
          <Button
            type="button"
            variant="primary"
            className="w-full finnova-btn-primary py-3"
            onClick={() => navigate('/login', { replace: true })}
            rightIcon={<ArrowRight className="h-4 w-4" />}
          >
            Sign In
          </Button>
        </div>
      </div>
    );
  }

  // ----------------------------------------------------
  // Reset Password Form State
  // ----------------------------------------------------
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-200">
      <div className="space-y-1.5 text-center">
        <h2 className="text-xl font-bold tracking-tight text-[#181534]">
          Create a new password
        </h2>
        <p className="text-xs text-slate-500 font-medium leading-relaxed max-w-sm mx-auto">
          Choose a strong password for your Vishleshan AI account.
        </p>
      </div>

      {formError && (
        <div className="flex items-start gap-2.5 rounded-2xl border border-rose-200 bg-rose-50 p-3.5 text-xs font-semibold text-rose-700">
          <AlertCircle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
          <span className="leading-relaxed">{formError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {/* New Password */}
        <div>
          <Input
            label="New Password"
            type={showPassword ? 'text' : 'password'}
            placeholder="At least 6 characters"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (passwordError) setPasswordError(null);
            }}
            leftIcon={<Lock className="h-4 w-4" />}
            rightIcon={
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-slate-400 hover:text-slate-600 focus:outline-none"
                title={showPassword ? 'Hide password' : 'Show password'}
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            }
            error={passwordError || undefined}
            required
            autoComplete="new-password"
            disabled={isLoading}
          />

          {/* Password Strength Indicator */}
          {password.length > 0 && (
            <div className="mt-2 space-y-1.5">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-400 font-medium">Strength:</span>
                <span
                  className={`font-bold capitalize ${
                    strength.level === 'weak'
                      ? 'text-rose-500'
                      : strength.level === 'fair'
                      ? 'text-amber-500'
                      : strength.level === 'good'
                      ? 'text-[#5b5dfa]'
                      : 'text-emerald-500'
                  }`}
                >
                  {strength.label}
                </span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className={`h-full transition-all duration-300 ${strength.color}`}
                  style={{ width: `${strength.score}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Confirm Password */}
        <Input
          label="Confirm New Password"
          type={showConfirmPassword ? 'text' : 'password'}
          placeholder="Re-enter your new password"
          value={confirmPassword}
          onChange={(e) => {
            setConfirmPassword(e.target.value);
            if (confirmError) setConfirmError(null);
          }}
          leftIcon={<Lock className="h-4 w-4" />}
          rightIcon={
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="text-slate-400 hover:text-slate-600 focus:outline-none"
              title={showConfirmPassword ? 'Hide password' : 'Show password'}
              tabIndex={-1}
            >
              {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          }
          error={confirmError || undefined}
          required
          autoComplete="new-password"
          disabled={isLoading}
        />

        <Button
          type="submit"
          variant="primary"
          className="w-full finnova-btn-primary py-3"
          isLoading={isLoading}
          rightIcon={<ArrowRight className="h-4 w-4" />}
        >
          {isLoading ? 'Updating...' : 'Update Password'}
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
