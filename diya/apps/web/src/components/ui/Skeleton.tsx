'use client';

import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'bg-diya-border/50 rounded animate-pulse',
        className
      )}
    />
  );
}

export function MetricCardSkeleton() {
  return (
    <div className="card">
      <div className="card-body">
        <div className="flex items-start justify-between mb-4">
          <Skeleton className="w-10 h-10 rounded-lg" />
        </div>
        <Skeleton className="h-8 w-16 mb-2" />
        <Skeleton className="h-3 w-24" />
      </div>
    </div>
  );
}

export function ConflictCardSkeleton() {
  return (
    <div className="card">
      <div className="card-body">
        <div className="flex items-start gap-3 mb-3">
          <Skeleton className="w-9 h-9 rounded-lg flex-shrink-0" />
          <div className="flex-1">
            <Skeleton className="h-4 w-32 mb-2" />
            <Skeleton className="h-3 w-48" />
          </div>
        </div>
        <div className="flex gap-2 mb-3">
          <Skeleton className="h-6 w-20 rounded" />
          <Skeleton className="h-6 w-24 rounded" />
          <Skeleton className="h-6 w-28 rounded" />
        </div>
        <div className="flex gap-4">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-3 w-32" />
        </div>
      </div>
    </div>
  );
}

export function TableRowSkeleton({ cols = 5 }: { cols?: number }) {
  return (
    <div className="flex items-center gap-4 px-4 py-3 border-b border-diya-border">
      {Array.from({ length: cols }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn(
            'h-3',
            i === 0 ? 'w-16' : i === 1 ? 'w-32' : 'w-20'
          )}
        />
      ))}
    </div>
  );
}

export function AgentActivitySkeleton() {
  return (
    <div className="flex items-start gap-3 px-4 py-3">
      <Skeleton className="w-8 h-8 rounded-lg flex-shrink-0" />
      <div className="flex-1">
        <Skeleton className="h-3 w-36 mb-2" />
        <Skeleton className="h-3 w-full mb-1.5" />
        <Skeleton className="h-3 w-3/4" />
        <div className="flex gap-3 mt-2">
          <Skeleton className="h-2.5 w-12" />
          <Skeleton className="h-2.5 w-16" />
        </div>
      </div>
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="page-container">
      <div className="mb-6">
        <Skeleton className="h-7 w-48 mb-2" />
        <Skeleton className="h-4 w-80" />
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <MetricCardSkeleton key={i} />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <div className="card h-[280px]" />
        </div>
        <div className="card h-[400px]" />
      </div>
    </div>
  );
}
