import React from 'react';
import { Loader2 } from 'lucide-react';
import { GoogleIcon } from './GoogleIcon';

export interface GoogleButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
}

export const GoogleButton: React.FC<GoogleButtonProps> = ({
  isLoading = false,
  disabled,
  onClick,
  className = '',
  ...props
}) => {
  return (
    <button
      type="button"
      aria-label="Continue with Google"
      disabled={disabled || isLoading}
      onClick={onClick}
      className={`w-full h-[54px] sm:h-[56px] min-h-[54px] sm:min-h-[56px] px-4 sm:px-6 rounded-full bg-white border border-slate-200/90 hover:border-slate-300 hover:bg-slate-50/80 shadow-xs hover:shadow-sm flex flex-row items-center justify-center gap-2.5 sm:gap-3 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#5b5dfa] focus-visible:ring-offset-2 active:scale-[0.99] disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer ${className}`}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="h-5 w-5 animate-spin text-[#5b5dfa] shrink-0" />
      ) : (
        <GoogleIcon className="h-5 w-5 shrink-0" />
      )}
      <span className="text-[14px] sm:text-[15px] font-semibold text-[#181534] tracking-normal select-none leading-none truncate">
        {isLoading ? 'Connecting to Google...' : 'Continue with Google'}
      </span>
    </button>
  );
};
