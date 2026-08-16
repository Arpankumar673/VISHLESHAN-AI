import React, { forwardRef } from 'react';
import { Loader2 } from 'lucide-react';

export type ButtonVariant =
  | 'primary'
  | 'white'
  | 'dark'
  | 'secondary'
  | 'outline'
  | 'ghost'
  | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  pill?: boolean;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      className = '',
      variant = 'primary',
      size = 'md',
      pill = true,
      isLoading = false,
      leftIcon,
      rightIcon,
      disabled,
      type = 'button',
      ...props
    },
    ref
  ) => {
    const roundedStyle = pill ? 'rounded-full' : 'rounded-2xl';

    const baseStyles =
      `inline-flex items-center justify-center font-semibold transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#5b5dfa] focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed select-none cursor-pointer ${roundedStyle}`;

    const sizeStyles = {
      sm: 'text-xs px-3.5 py-1.5 gap-1.5',
      md: 'text-sm px-5 py-2.5 gap-2',
      lg: 'text-base px-7 py-3.5 gap-2.5',
    };

    const variantStyles = {
      primary:
        'bg-[#5b5dfa] text-white hover:bg-[#4f46e5] shadow-md shadow-indigo-500/25 active:scale-[0.98]',
      white:
        'bg-white text-[#181534] hover:bg-slate-50 border border-slate-200/80 shadow-xs active:scale-[0.98]',
      dark:
        'bg-[#181534] text-white hover:bg-[#232048] shadow-md active:scale-[0.98]',
      secondary:
        'bg-slate-100 text-[#181534] hover:bg-slate-200/80 border border-slate-200 active:scale-[0.98]',
      outline:
        'border border-slate-300/80 bg-transparent text-[#181534] hover:bg-slate-100 active:scale-[0.98]',
      ghost:
        'bg-transparent text-slate-600 hover:bg-slate-200/60 hover:text-[#181534]',
      danger:
        'bg-rose-50 text-rose-600 border border-rose-200 hover:bg-rose-100 active:scale-[0.98]',
    };

    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled || isLoading}
        className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin text-current" />
        ) : (
          leftIcon
        )}
        <span>{children}</span>
        {!isLoading && rightIcon}
      </button>
    );
  }
);

Button.displayName = 'Button';
