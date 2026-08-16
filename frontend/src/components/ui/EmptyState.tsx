import React from 'react';
import { Card } from './Card';
import { Button } from './Button';

export interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  className = '',
}) => {
  return (
    <Card className={`p-8 sm:p-12 text-center ${className}`}>
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-800/80 border border-slate-700/60 text-slate-400">
        {icon}
      </div>
      <h3 className="mt-4 text-base sm:text-lg font-semibold text-slate-100">
        {title}
      </h3>
      <p className="mx-auto mt-2 max-w-md text-sm text-slate-400">
        {description}
      </p>
      {actionLabel && onAction && (
        <div className="mt-6 flex justify-center">
          <Button variant="primary" onClick={onAction}>
            {actionLabel}
          </Button>
        </div>
      )}
    </Card>
  );
};
