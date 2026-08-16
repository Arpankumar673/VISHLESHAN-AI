import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Mail, Lock, AlertCircle, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { GoogleButton } from '../components/ui/GoogleButton';

export const Login: React.FC = () => {
  const { signIn, signInWithGoogle } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const [emailError, setEmailError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  const fromLocation =
    (location.state as { from?: { pathname?: string } })?.from?.pathname || '/dashboard';

  const validateForm = (): boolean => {
    let isValid = true;
    const trimmedEmail = email.trim();

    if (!trimmedEmail) {
      setEmailError('Please enter your email address.');
      isValid = false;
    } else {
      setEmailError(null);
    }

    if (!password) {
      setPasswordError('Please enter your password.');
      isValid = false;
    } else {
      setPasswordError(null);
    }

    return isValid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    const { error: signInError } = await signIn({ email: email.trim(), password });
    setIsSubmitting(false);

    if (signInError) {
      if (
        signInError.toLowerCase().includes('invalid login credentials') ||
        signInError.toLowerCase().includes('invalid credentials')
      ) {
        setError('Email or password is incorrect.');
      } else if (signInError.toLowerCase().includes('email not confirmed')) {
        setError('Please verify your email before signing in.');
      } else {
        setError(signInError);
      }
    } else {
      navigate(fromLocation, { replace: true });
    }
  };

  const handleGoogleSignIn = async () => {
    setError(null);
    setIsGoogleLoading(true);
    const { error: googleError } = await signInWithGoogle();
    if (googleError) {
      setIsGoogleLoading(false);
      if (googleError.toLowerCase().includes('cancelled')) {
        setError('Google sign-in was cancelled.');
      } else {
        setError("We couldn't complete Google sign-in. Please try again.");
      }
    }
  };

  const isAnyLoading = isSubmitting || isGoogleLoading;

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-200">
      <div className="space-y-1.5 text-center">
        <h2 className="text-xl font-bold tracking-tight text-[#181534]">
          Welcome Back
        </h2>
        <p className="text-xs text-slate-500 font-medium">
          Sign in to access evidence-backed company intelligence
        </p>
      </div>

      {error && (
        <div className="flex items-start gap-2.5 rounded-2xl border border-rose-200 bg-rose-50 p-3.5 text-xs font-semibold text-rose-700">
          <AlertCircle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
          <span className="leading-relaxed">{error}</span>
        </div>
      )}

      {/* Google OAuth Button */}
      <GoogleButton
        onClick={handleGoogleSignIn}
        disabled={isAnyLoading}
        isLoading={isGoogleLoading}
      />

      {/* Divider */}
      <div className="relative flex items-center justify-center">
        <div className="w-full border-t border-slate-200" />
        <span className="absolute bg-white px-3 text-[11px] font-bold uppercase tracking-wider text-slate-400">
          OR
        </span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <Input
          label="Email Address"
          type="email"
          placeholder="name@university.edu or name@company.com"
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

        <div className="space-y-1">
          <Input
            label="Password"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••••••"
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
            autoComplete="current-password"
            disabled={isAnyLoading}
          />
          <div className="flex justify-end pt-0.5">
            <Link
              to="/forgot-password"
              className="text-xs font-semibold text-[#5b5dfa] hover:underline"
            >
              Forgot password?
            </Link>
          </div>
        </div>

        <Button
          type="submit"
          variant="primary"
          className="w-full finnova-btn-primary py-3"
          isLoading={isSubmitting}
          disabled={isAnyLoading}
          rightIcon={<ArrowRight className="h-4 w-4" />}
        >
          {isSubmitting ? 'Signing in...' : 'Sign In'}
        </Button>
      </form>

      <div className="pt-2 text-center text-xs text-slate-500 border-t border-slate-100">
        <p>
          Don't have an account?{' '}
          <Link
            to="/signup"
            className="font-bold text-[#5b5dfa] hover:underline"
          >
            Create Account
          </Link>
        </p>
      </div>
    </div>
  );
};
