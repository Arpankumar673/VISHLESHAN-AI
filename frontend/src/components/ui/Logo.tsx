import React from 'react';

export interface LogoProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'full' | 'horizontal' | 'icon';
  theme?: 'dark' | 'light' | 'auto';
  className?: string;
  showSubtitle?: boolean;
}

export const Logo: React.FC<LogoProps> = ({
  size = 'md',
  variant = 'full',
  theme = 'auto',
  className = '',
  showSubtitle = true,
}) => {
  const sizeMap = {
    xs: { iconSize: 'h-6 w-6 rounded-lg', text: 'text-sm', sub: 'text-[9px]' },
    sm: { iconSize: 'h-8 w-8 rounded-xl', text: 'text-base', sub: 'text-[10px]' },
    md: { iconSize: 'h-11 w-11 rounded-2xl', text: 'text-xl', sub: 'text-[11px]' },
    lg: { iconSize: 'h-14 w-14 rounded-2xl', text: 'text-2xl', sub: 'text-xs' },
    xl: { iconSize: 'h-20 w-20 rounded-3xl', text: 'text-3xl', sub: 'text-sm' },
  };

  const currentSize = sizeMap[size];

  const iconImage = (
    <div className={`relative shrink-0 overflow-hidden shadow-md shadow-indigo-950/10 transition-transform duration-300 group-hover:scale-105 ${currentSize.iconSize}`}>
      <img
        src="/logo.png"
        alt="Vishleshan AI Logo"
        className="h-full w-full object-cover"
        loading="eager"
      />
    </div>
  );

  if (variant === 'icon') {
    return <div className={`inline-flex items-center justify-center ${className}`}>{iconImage}</div>;
  }

  const isLightMode = theme === 'light';

  return (
    <div className={`inline-flex items-center gap-3 group ${className}`}>
      {iconImage}
      <div className="flex flex-col text-left">
        <div className="flex items-center gap-1.5">
          <span
            className={`font-extrabold tracking-tight ${currentSize.text} ${
              isLightMode ? 'text-[#181534]' : 'text-white'
            }`}
          >
            VISHLESHAN
          </span>
          <span className="rounded-md bg-gradient-to-r from-[#5b5dfa] to-[#7c3aed] px-1.5 py-0.5 text-[10px] font-black uppercase tracking-wider text-white shadow-xs">
            AI
          </span>
        </div>
        {variant === 'full' && showSubtitle && (
          <span
            className={`font-medium tracking-wide leading-tight ${currentSize.sub} ${
              isLightMode ? 'text-slate-500' : 'text-slate-400'
            }`}
          >
            Intelligence & Verification Platform
          </span>
        )}
      </div>
    </div>
  );
};
