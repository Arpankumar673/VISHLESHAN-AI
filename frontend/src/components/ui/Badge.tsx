import React from 'react';

export type BadgeVariant = 'slate' | 'cyan' | 'blue' | 'emerald' | 'amber' | 'purple' | 'rose';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  className = '',
  variant = 'slate',
  size = 'md',
  icon,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center font-medium rounded-full border transition-colors';

  const sizeStyles = {
    sm: 'text-[10px] px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5',
  };

  const variantStyles = {
    slate: 'bg-slate-800/80 text-slate-300 border-slate-700/80',
    cyan: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
    blue: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    rose: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
  };

  return (
    <span
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {icon}
      <span>{children}</span>
    </span>
  );
};
