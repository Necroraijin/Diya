'use client';

import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: { value: number; label: string };
  accentColor?: string;
}

export default function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  accentColor,
}: MetricCardProps) {
  return (
    <div className="card group hover:border-diya-border-light transition-colors duration-200 animate-slide-up">
      <div className="card-body">
        <div className="flex items-start justify-between mb-3 sm:mb-4">
          <div
            className={cn(
              'w-9 h-9 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center border',
              accentColor || 'bg-diya-surface border-diya-border'
            )}
          >
            <Icon className="w-4 h-4 sm:w-5 sm:h-5 text-diya-text-secondary" strokeWidth={1.5} />
          </div>
          {trend && (
            <span
              className={cn(
                'text-[10px] sm:text-xs font-medium px-1.5 sm:px-2 py-0.5 rounded-full',
                trend.value > 0
                  ? 'text-diya-conflict bg-diya-conflict-dim'
                  : 'text-diya-resolved bg-diya-resolved-dim'
              )}
            >
              {trend.value > 0 ? '+' : ''}
              {trend.value}%
            </span>
          )}
        </div>
        <div className="metric-value mb-1">{value}</div>
        <div className="data-label">{title}</div>
        {subtitle && (
          <div className="text-[10px] sm:text-xs text-diya-text-muted mt-1.5 sm:mt-2 leading-relaxed">{subtitle}</div>
        )}
      </div>
      <div className="h-px bg-gradient-to-r from-transparent via-white/5 to-transparent group-hover:via-white/10 transition-all duration-300" />
    </div>
  );
}
