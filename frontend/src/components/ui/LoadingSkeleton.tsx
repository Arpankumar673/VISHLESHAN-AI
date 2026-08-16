import React from 'react';

export interface LoadingSkeletonProps {
  className?: string;
  variant?: 'text' | 'rect' | 'circle';
  count?: number;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  className = '',
  variant = 'text',
  count = 1,
}) => {
  const baseStyles = 'animate-pulse bg-slate-800/80';

  const variantStyles = {
    text: 'h-4 w-full rounded-md',
    rect: 'h-24 w-full rounded-xl',
    circle: 'h-10 w-10 rounded-full',
  };

  const items = Array.from({ length: count }, (_, i) => i);

  return (
    <>
      {items.map((key) => (
        <div
          key={key}
          className={`${baseStyles} ${variantStyles[variant]} ${className}`}
        />
      ))}
    </>
  );
};
