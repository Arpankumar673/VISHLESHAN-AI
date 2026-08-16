import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, User, AlertCircle, ArrowRight, ShieldCheck } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

export const Register: React.FC = () => {
  const { signUp } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!fullName.trim()) {
      setError('Please enter your full name');
      return;
    }
    if (!email.trim()) {
      setError('Please enter your email address');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);
    const { error: signUpError } = await signUp({
      email,
      password,
      fullName: fullName.trim(),
    });
    setIsLoading(false);

    if (signUpError) {
      setError(signUpError);
    } else {
      navigate('/dashboard', { replace: true });
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-1 text-center">
        <h2 className="text-xl font-bold tracking-tight text-[#181534]">
          Create an Account
        </h2>
        <p className="text-xs text-slate-500 font-medium">
          Join Vishleshan AI to analyze and verify organizations
        </p>
      </div>

      {error && (
        <div className="flex items-start gap-2.5 rounded-2xl border border-rose-200 bg-rose-50 p-3.5 text-xs font-semibold text-rose-700">
          <AlertCircle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
          <span className="leading-relaxed">{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Full Name"
          type="text"
          placeholder="e.g. John Doe"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          leftIcon={<User className="h-4 w-4" />}
          required
          autoComplete="name"
          disabled={isLoading}
        />

        <Input
          label="Email Address"
          type="email"
          placeholder="name@university.edu or name@company.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          leftIcon={<Mail className="h-4 w-4" />}
          required
          autoComplete="email"
          disabled={isLoading}
        />

        <Input
          label="Password"
          type="password"
          placeholder="At least 6 characters"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          leftIcon={<Lock className="h-4 w-4" />}
          required
          autoComplete="new-password"
          disabled={isLoading}
        />

        <Input
          label="Confirm Password"
          type="password"
          placeholder="Re-enter password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          leftIcon={<Lock className="h-4 w-4" />}
          required
          autoComplete="new-password"
          disabled={isLoading}
        />

        <div className="rounded-2xl bg-indigo-50 p-3 text-[11px] text-indigo-900 font-medium flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-[#5b5dfa] shrink-0" />
          <span>Role defaults to Analyst. Admin capabilities can be provisioned.</span>
        </div>

        <Button
          type="submit"
          variant="primary"
          className="w-full finnova-btn-primary py-3"
          isLoading={isLoading}
          rightIcon={<ArrowRight className="h-4 w-4" />}
        >
          Create Account
        </Button>
      </form>

      <div className="pt-2 text-center text-xs text-slate-500 border-t border-slate-100 space-y-2">
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
