import React, { forwardRef } from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  pill?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      pill = false,
      className = '',
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);
    const roundedStyle = pill ? 'rounded-full' : 'rounded-2xl';

    return (
      <div className="w-full space-y-1.5 text-left">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-bold text-[#181534] tracking-wide"
          >
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {leftIcon && (
            <div className="pointer-events-none absolute left-4 flex items-center text-slate-400">
              {leftIcon}
            </div>
          )}
          <input
            id={inputId}
            ref={ref}
            className={`w-full ${roundedStyle} border bg-white px-4 py-3 text-sm font-medium text-[#181534] placeholder:text-slate-400 placeholder:font-normal transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[#5b5dfa] focus:border-[#5b5dfa] disabled:opacity-50 disabled:cursor-not-allowed shadow-xs ${
              leftIcon ? 'pl-11' : ''
            } ${rightIcon ? 'pr-11' : ''} ${
              error
                ? 'border-rose-300 focus:ring-rose-400 focus:border-rose-400 text-rose-700'
                : 'border-slate-200 hover:border-slate-300'
            } ${className}`}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-4 flex items-center text-slate-400">
              {rightIcon}
            </div>
          )}
        </div>
        {error ? (
          <p className="text-xs font-semibold text-rose-500">{error}</p>
        ) : helperText ? (
          <p className="text-xs text-slate-500 font-medium">{helperText}</p>
        ) : null}
      </div>
    );
  }
);

Input.displayName = 'Input';
