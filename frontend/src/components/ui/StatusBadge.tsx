import React from 'react';
import { CheckCircle2, HelpCircle, AlertTriangle, XCircle } from 'lucide-react';
import type { VerificationStatus } from '../../types';

export interface StatusBadgeProps {
  status: VerificationStatus;
  size?: 'sm' | 'md';
  className?: string;
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  className = '',
  showIcon = true,
}) => {
  const configMap: Record<
    VerificationStatus,
    {
      label: string;
      icon: React.ComponentType<{ className?: string }>;
      styles: string;
      dotColor: string;
    }
  > = {
    verified: {
      label: 'Verified',
      icon: CheckCircle2,
      styles: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
      dotColor: 'bg-emerald-500',
    },
    unverified: {
      label: 'Unverified',
      icon: HelpCircle,
      styles: 'bg-amber-50 text-amber-700 border-amber-200/80',
      dotColor: 'bg-amber-500',
    },
    conflicting: {
      label: 'Conflicting',
      icon: AlertTriangle,
      styles: 'bg-purple-50 text-purple-700 border-purple-200/80',
      dotColor: 'bg-purple-500',
    },
    unable_to_verify: {
      label: 'Unable to Verify',
      icon: XCircle,
      styles: 'bg-slate-100 text-slate-600 border-slate-200',
      dotColor: 'bg-slate-400',
    },
  };

  const config = configMap[status] || configMap.unverified;
  const Icon = config.icon;

  const sizeStyles = {
    sm: 'text-[10px] px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5',
  };

  return (
    <span
      className={`inline-flex items-center font-bold rounded-full border shadow-2xs ${sizeStyles[size]} ${config.styles} ${className}`}
    >
      {showIcon && <Icon className={size === 'sm' ? 'h-3 w-3' : 'h-3.5 w-3.5'} />}
      <span>{config.label}</span>
    </span>
  );
};
