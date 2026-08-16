import React from 'react';
import { ShieldCheck, AlertCircle, AlertTriangle, ShieldAlert, HelpCircle } from 'lucide-react';
import type { RiskLevel } from '../../types';

export interface RiskBadgeProps {
  level: RiskLevel;
  size?: 'sm' | 'md';
  className?: string;
  showIcon?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  level,
  size = 'md',
  className = '',
  showIcon = true,
}) => {
  const configMap: Record<
    RiskLevel,
    {
      label: string;
      icon: React.ComponentType<{ className?: string }>;
      styles: string;
    }
  > = {
    low: {
      label: 'Low Risk',
      icon: ShieldCheck,
      styles: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
    },
    medium: {
      label: 'Medium Risk',
      icon: AlertCircle,
      styles: 'bg-amber-50 text-amber-700 border-amber-200/80',
    },
    high: {
      label: 'High Risk',
      icon: AlertTriangle,
      styles: 'bg-orange-50 text-orange-700 border-orange-200/80',
    },
    critical: {
      label: 'Critical Risk',
      icon: ShieldAlert,
      styles: 'bg-rose-50 text-rose-700 border-rose-200/80',
    },
    unknown: {
      label: 'Risk Unknown',
      icon: HelpCircle,
      styles: 'bg-slate-100 text-slate-600 border-slate-200',
    },
  };

  const config = configMap[level] || configMap.unknown;
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
