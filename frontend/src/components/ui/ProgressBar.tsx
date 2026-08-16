import React from 'react';

export interface ProgressBarProps {
  value: number; // 0 to 100
  max?: number;
  label?: string;
  sublabel?: string;
  showPercentage?: boolean;
  color?: 'cyan' | 'emerald' | 'amber' | 'rose' | 'purple' | 'blue';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  label,
  sublabel,
  showPercentage = true,
  color = 'cyan',
  size = 'md',
  className = '',
}) => {
  const percentage = Math.min(Math.max(Math.round((value / max) * 100), 0), 100);

  const sizeStyles = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  const colorStyles = {
    cyan: 'bg-gradient-to-r from-cyan-500 to-blue-500',
    emerald: 'bg-gradient-to-r from-emerald-500 to-teal-400',
    amber: 'bg-gradient-to-r from-amber-500 to-orange-400',
    rose: 'bg-gradient-to-r from-rose-500 to-red-500',
    purple: 'bg-gradient-to-r from-purple-500 to-indigo-500',
    blue: 'bg-gradient-to-r from-blue-500 to-cyan-400',
  };

  return (
    <div className={`w-full space-y-1.5 ${className}`}>
      {(label || showPercentage) && (
        <div className="flex items-center justify-between text-xs font-medium">
          <div className="flex items-center gap-2">
            {label && <span className="text-slate-300">{label}</span>}
            {sublabel && <span className="text-slate-500">{sublabel}</span>}
          </div>
          {showPercentage && (
            <span className="font-semibold text-slate-200">{percentage}%</span>
          )}
        </div>
      )}
      <div className={`w-full overflow-hidden rounded-full bg-slate-800/90 p-0.5 border border-slate-700/50 ${sizeStyles[size]}`}>
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${colorStyles[color]}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
