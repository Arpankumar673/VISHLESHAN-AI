import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  variant?: 'light' | 'dark' | 'glass' | 'panel';
  glow?: 'cyan' | 'blue' | 'purple' | 'indigo' | 'none';
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  hover = false,
  variant = 'light',
  glow = 'none',
  ...props
}) => {
  const baseStyles = 'rounded-3xl transition-all duration-200';

  const variantStyles = {
    light: 'bg-white border border-slate-200/80 shadow-sm text-[#181534]',
    dark: 'bg-[#181534] border border-slate-800 shadow-xl text-white',
    panel: 'bg-[#232048] border border-white/10 shadow-md text-white',
    glass: 'bg-white/80 backdrop-blur-md border border-slate-200/80 shadow-lg text-[#181534]',
  };

  const hoverStyles = hover
    ? variant === 'dark' || variant === 'panel'
      ? 'hover:border-indigo-500/40 hover:shadow-indigo-500/10 hover:-translate-y-0.5'
      : 'hover:border-indigo-200 hover:shadow-md hover:-translate-y-0.5'
    : '';

  const glowStyles = {
    none: '',
    cyan: 'border-cyan-400/40 shadow-lg shadow-cyan-500/10',
    blue: 'border-blue-400/40 shadow-lg shadow-blue-500/10',
    purple: 'border-purple-400/40 shadow-lg shadow-purple-500/10',
    indigo: 'border-[#5b5dfa]/40 shadow-lg shadow-indigo-500/15',
  };

  return (
    <div
      className={`${baseStyles} ${variantStyles[variant]} ${hoverStyles} ${glowStyles[glow]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = '',
  ...props
}) => (
  <div className={`p-6 border-b border-slate-100/80 ${className}`} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  children,
  className = '',
  ...props
}) => (
  <h3 className={`text-lg font-bold text-inherit tracking-tight ${className}`} {...props}>
    {children}
  </h3>
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  children,
  className = '',
  ...props
}) => (
  <p className={`mt-1 text-xs text-slate-400 font-medium ${className}`} {...props}>
    {children}
  </p>
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = '',
  ...props
}) => (
  <div className={`p-6 ${className}`} {...props}>
    {children}
  </div>
);

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = '',
  ...props
}) => (
  <div className={`p-6 border-t border-slate-100/80 rounded-b-3xl ${className}`} {...props}>
    {children}
  </div>
);
