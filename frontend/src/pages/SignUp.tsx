import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Mail,
  Lock,
  User,
  AlertCircle,
  ArrowRight,
  Eye,
  EyeOff,
  RefreshCw,
  ArrowLeft,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { GoogleIcon } from '../components/ui/GoogleIcon';

export const SignUp: React.FC = () => {
  const { signUp, signInWithGoogle, resendVerificationEmail } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Field validation errors
  const [fullNameError, setFullNameError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [confirmPasswordError, setConfirmPasswordError] = useState<string | null>(null);
  const [generalError, setGeneralError] = useState<string | null>(null);

  // Loading states
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  // Confirmation email state
  const [needsConfirmation, setNeedsConfirmation] = useState(false);
  const [confirmedEmail, setConfirmedEmail] = useState('');
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

  const validateForm = (): boolean => {
    let isValid = true;

    // Full Name
    if (!fullName.trim()) {
      setFullNameError('Please enter your name.');
      isValid = false;
    } else {
      setFullNameError(null);
    }

    // Email
    const trimmedEmail = email.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!trimmedEmail) {
      setEmailError('Please enter your email address.');
      isValid = false;
    } else if (!emailRegex.test(trimmedEmail)) {
      setEmailError('Please enter a valid email address.');
      isValid = false;
    } else {
      setEmailError(null);
    }

    // Password
    if (!password) {
      setPasswordError('Please enter a password.');
      isValid = false;
    } else if (password.length < 6) {
      setPasswordError('Password must be at least 6 characters.');
      isValid = false;
    } else {
      setPasswordError(null);
    }

    // Confirm Password
    if (!confirmPassword) {
      setConfirmPasswordError('Please confirm your password.');
      isValid = false;
    } else if (password !== confirmPassword) {
      setConfirmPasswordError('Passwords do not match.');
      isValid = false;
    } else {
      setConfirmPasswordError(null);
    }

    return isValid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeneralError(null);

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    const result = await signUp({
      email: email.trim(),
      password,
      fullName: fullName.trim(),
    });
    setIsSubmitting(false);

    if (result.error) {
      if (
        result.error.toLowerCase().includes('already registered') ||
        result.error.toLowerCase().includes('already exists')
      ) {
        setGeneralError('This email is already associated with an account. Try signing in.');
      } else if (result.error.toLowerCase().includes('weak')) {
        setGeneralError('Please choose a stronger password.');
      } else {
        setGeneralError(result.error);
      }
    } else if (result.needsEmailConfirmation) {
      setConfirmedEmail(result.userEmail || email.trim());
      setNeedsConfirmation(true);
      setCooldown(30);
    } else {
      navigate('/dashboard', { replace: true });
    }
  };

  const handleGoogleSignUp = async () => {
    setGeneralError(null);
    setIsGoogleLoading(true);
    const { error: googleError } = await signInWithGoogle();
    if (googleError) {
      setIsGoogleLoading(false);
      if (googleError.toLowerCase().includes('cancelled')) {
        setGeneralError('Google sign-in was cancelled.');
      } else {
        setGeneralError("We couldn't complete Google sign-in. Please try again.");
      }
    }
  };

  const handleResend = async () => {
    if (cooldown > 0 || !confirmedEmail || isSubmitting) return;

    setGeneralError(null);
    setIsSubmitting(true);
    const { error: resendError } = await resendVerificationEmail(confirmedEmail);
    setIsSubmitting(false);

    if (resendError) {
      setGeneralError("We couldn't resend the verification email. Please try again.");
    } else {
      setCooldown(30);
    }
  };

  // ----------------------------------------------------
  // Email Confirmation State
  // ----------------------------------------------------
  if (needsConfirmation) {
    return (
      <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-200">
        <div className="text-center space-y-2">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 border border-indigo-100 text-[#5b5dfa] shadow-xs">
            <Mail className="h-7 w-7" />
          </div>
          <h2 className="text-xl font-bold tracking-tight text-[#181534]">
            Check your email
          </h2>
          <p className="text-xs text-slate-500 font-medium max-w-sm mx-auto leading-relaxed">
            We've sent a verification link to:
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 p-3.5 text-center">
          <span className="text-sm font-bold font-mono text-[#181534] break-all">
            {confirmedEmail}
          </span>
        </div>

        <div className="rounded-2xl border border-indigo-100 bg-indigo-50/50 p-3.5 text-xs text-slate-600 leading-relaxed text-center font-medium">
          Please verify your email before signing in. Check your inbox and spam folder.
        </div>

        {generalError && (
          <div className="flex items-start gap-2.5 rounded-2xl border border-rose-200 bg-rose-50 p-3.5 text-xs font-semibold text-rose-700">
            <AlertCircle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
            <span className="leading-relaxed">{generalError}</span>
          </div>
        )}

        <div className="space-y-3 pt-1">
          <a href={`mailto:${confirmedEmail}`} className="w-full inline-flex">
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
                disabled={isSubmitting}
                className="inline-flex items-center gap-1.5 text-xs font-bold text-[#5b5dfa] hover:underline disabled:opacity-50"
              >
                <RefreshCw className={`h-3 w-3 ${isSubmitting ? 'animate-spin' : ''}`} />
                <span>Resend verification email</span>
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
  // Main Sign Up Form
  // ----------------------------------------------------
  const isAnyLoading = isSubmitting || isGoogleLoading;

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-200">
      <div className="space-y-1.5 text-center">
        <h2 className="text-xl font-bold tracking-tight text-[#181534]">
          Create your Vishleshan AI account
        </h2>
        <p className="text-xs text-slate-500 font-medium leading-relaxed">
          Create an account to research, verify, and analyze companies.
        </p>
      </div>

      {generalError && (
        <div className="flex items-start gap-2.5 rounded-2xl border border-rose-200 bg-rose-50 p-3.5 text-xs font-semibold text-rose-700">
          <AlertCircle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
          <span className="leading-relaxed">{generalError}</span>
        </div>
      )}

      {/* Google OAuth Button */}
      <Button
        type="button"
        variant="white"
        className="w-full finnova-btn-white py-3 justify-center gap-3"
        onClick={handleGoogleSignUp}
        disabled={isAnyLoading}
        isLoading={isGoogleLoading}
      >
        <GoogleIcon className="h-4 w-4" />
        <span>{isGoogleLoading ? 'Connecting to Google...' : 'Continue with Google'}</span>
      </Button>

      {/* Divider */}
      <div className="relative flex items-center justify-center">
        <div className="w-full border-t border-slate-200" />
        <span className="absolute bg-white px-3 text-[11px] font-bold uppercase tracking-wider text-slate-400">
          OR
        </span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {/* Full Name */}
        <Input
          label="Full Name"
          type="text"
          placeholder="Enter your name"
          value={fullName}
          onChange={(e) => {
            setFullName(e.target.value);
            if (fullNameError) setFullNameError(null);
          }}
          leftIcon={<User className="h-4 w-4" />}
          error={fullNameError || undefined}
          required
          autoComplete="name"
          disabled={isAnyLoading}
        />

        {/* Email */}
        <Input
          label="Email Address"
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            if (emailError) setEmailError(null);
          }}
          leftIcon={<Mail className="h-4 w-4" />}
          error={emailError || undefined}
          required
          autoComplete="email"
          disabled={isAnyLoading}
        />

        {/* Password */}
        <Input
          label="Password"
          type={showPassword ? 'text' : 'password'}
          placeholder="Enter password"
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
          disabled={isAnyLoading}
        />

        {/* Confirm Password */}
        <Input
          label="Confirm Password"
          type={showConfirmPassword ? 'text' : 'password'}
          placeholder="Confirm password"
          value={confirmPassword}
          onChange={(e) => {
            setConfirmPassword(e.target.value);
            if (confirmPasswordError) setConfirmPasswordError(null);
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
          error={confirmPasswordError || undefined}
          required
          autoComplete="new-password"
          disabled={isAnyLoading}
        />

        <Button
          type="submit"
          variant="primary"
          className="w-full finnova-btn-primary py-3"
          isLoading={isSubmitting}
          disabled={isAnyLoading}
          rightIcon={<ArrowRight className="h-4 w-4" />}
        >
          {isSubmitting ? 'Creating account...' : 'Create Account'}
        </Button>
      </form>

      <div className="pt-2 text-center text-xs text-slate-500 border-t border-slate-100">
        <p>
          Already have an account?{' '}
          <Link
            to="/login"
            className="font-bold text-[#5b5dfa] hover:underline"
          >
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
};
