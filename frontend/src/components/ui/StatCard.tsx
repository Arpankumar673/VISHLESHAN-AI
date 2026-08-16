import React from 'react';

export interface StatCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
  iconBgColor?: string;
  trend?: {
    value: string;
    isPositive?: boolean;
    label?: string;
  };
  chartType?: 'bars' | 'line' | 'cards' | 'none';
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  description,
  icon,
  iconBgColor = 'bg-indigo-50 text-[#5b5dfa]',
  trend,
  chartType = 'none',
  className = '',
}) => {
  return (
    <div
      className={`relative flex flex-col justify-between rounded-3xl bg-white border border-slate-200/80 p-6 shadow-sm hover:shadow-md transition-all duration-200 ${className}`}
    >
      <div>
        {/* Top Header */}
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-bold text-slate-500 tracking-wide">
            {title}
          </span>
          {icon && (
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-full ${iconBgColor} shadow-xs`}
            >
              {icon}
            </div>
          )}
        </div>

        {/* Big Bold Stat Value */}
        <div className="mt-3">
          <p className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#181534]">
            {value}
          </p>
        </div>

        {/* Trend Indicator */}
        {trend && (
          <div className="mt-1.5 flex items-center gap-1.5 text-xs font-semibold">
            <span
              className={
                trend.isPositive !== false
                  ? 'text-indigo-600 font-bold'
                  : 'text-rose-500 font-bold'
              }
            >
              {trend.isPositive !== false ? '↑' : '↓'} {trend.value}
            </span>
            <span className="text-slate-400 font-normal">
              {trend.label || 'from last month'}
            </span>
          </div>
        )}

        {description && !trend && (
          <p className="mt-1 text-xs text-slate-400 font-medium">{description}</p>
        )}
      </div>

      {/* Embedded Visual Chart Elements (Finnova Aesthetic) */}
      {chartType === 'bars' && (
        <div className="mt-4 flex items-end justify-between gap-1.5 pt-2 h-14">
          <div className="w-full bg-indigo-100 rounded-t-md h-[40%]" />
          <div className="w-full bg-indigo-200 rounded-t-md h-[60%]" />
          <div className="w-full bg-indigo-300 rounded-t-md h-[30%]" />
          <div className="w-full bg-[#818cf8] rounded-t-md h-[75%]" />
          <div className="w-full bg-[#6366f1] rounded-t-md h-[55%]" />
          <div className="w-full bg-[#5b5dfa] rounded-t-md h-[95%]" />
        </div>
      )}

      {chartType === 'line' && (
        <div className="mt-4 pt-2">
          <svg className="w-full h-14 overflow-visible" viewBox="0 0 100 40">
            <path
              d="M 5 32 Q 25 28, 40 22 T 70 12 T 95 6"
              fill="none"
              stroke="#5b5dfa"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
            {/* Sparkline nodes */}
            <circle cx="5" cy="32" r="3" fill="#ffffff" stroke="#5b5dfa" strokeWidth="2" />
            <circle cx="40" cy="22" r="3" fill="#ffffff" stroke="#5b5dfa" strokeWidth="2" />
            <circle cx="70" cy="12" r="3" fill="#ffffff" stroke="#5b5dfa" strokeWidth="2" />
            <circle cx="95" cy="6" r="3.5" fill="#5b5dfa" />
          </svg>
        </div>
      )}

      {chartType === 'cards' && (
        <div className="mt-4 flex items-center justify-between gap-1.5 pt-2">
          <div className="flex items-center gap-1 rounded-xl bg-slate-100/90 px-2.5 py-1.5 text-[10px] font-bold text-slate-700">
            <span>TLS Secure</span>
          </div>
          <div className="flex items-center gap-1 rounded-xl bg-[#5b5dfa] px-3 py-1.5 text-[10px] font-bold text-white shadow-xs">
            <span>Verified</span>
          </div>
          <div className="flex items-center gap-1 rounded-xl bg-slate-100/90 px-2.5 py-1.5 text-[10px] font-bold text-slate-700">
            <span>MCA Valid</span>
          </div>
        </div>
      )}
    </div>
  );
};
