'use client';

import { X, AlertTriangle, Clock, MapPin, IndianRupee } from 'lucide-react';
import { conflicts } from '@/lib/mock-data';
import { formatDate, formatCurrency, cn, getStatusColor, getStatusBg } from '@/lib/utils';

interface ConflictPanelProps {
  conflictId: string;
  onClose: () => void;
}

export default function ConflictPanel({ conflictId, onClose }: ConflictPanelProps) {
  const conflict = conflicts.find((c) => c.id === conflictId);
  if (!conflict) return null;

  return (
    <div className="absolute top-3 right-3 sm:top-4 sm:right-4 w-[calc(100%-24px)] sm:w-80 glass rounded-lg overflow-hidden animate-fade-in max-h-[calc(100%-24px)] overflow-y-auto">
      {/* Header */}
      <div className="px-4 py-3 border-b border-diya-border flex items-center justify-between sticky top-0 bg-diya-card/90 backdrop-blur-md z-10">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-diya-conflict" />
          <span className="text-sm font-medium">Conflict {conflict.id}</span>
        </div>
        <button
          onClick={onClose}
          className="w-6 h-6 rounded-md hover:bg-diya-card flex items-center justify-center transition-colors"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Status & Severity */}
      <div className="px-4 py-3 flex items-center gap-2 border-b border-diya-border flex-wrap">
        <span className={cn('badge', getStatusBg(conflict.status), getStatusColor(conflict.status))}>
          {conflict.status.toUpperCase()}
        </span>
        <span className={cn('badge', getStatusBg(conflict.severity), getStatusColor(conflict.severity))}>
          {conflict.severity.toUpperCase()}
        </span>
        <span className="badge bg-diya-card text-diya-text-secondary">
          {conflict.overlapType}
        </span>
      </div>

      {/* Affected works */}
      <div className="px-4 py-3 border-b border-diya-border">
        <span className="text-[10px] text-diya-text-muted uppercase tracking-wider block mb-2">
          Affected Works ({conflict.works.length})
        </span>
        <div className="space-y-2">
          {conflict.works.map((work) => (
            <div key={work.id} className="flex items-start gap-2">
              <div className="w-1 h-1 rounded-full bg-diya-text-muted mt-1.5 flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-xs font-medium truncate">{work.title}</p>
                <p className="text-[10px] text-diya-text-muted">
                  {work.deptName} &middot; {work.workType}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Details */}
      <div className="px-4 py-3 space-y-2.5 border-b border-diya-border">
        <div className="flex items-center gap-2 text-xs">
          <Clock className="w-3 h-3 text-diya-text-muted flex-shrink-0" />
          <span className="text-diya-text-muted">Window:</span>
          <span className="truncate">
            {formatDate(conflict.proposedWindow.start)} — {formatDate(conflict.proposedWindow.end)}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <IndianRupee className="w-3 h-3 text-diya-text-muted flex-shrink-0" />
          <span className="text-diya-text-muted">Savings:</span>
          <span className="text-diya-resolved font-medium">
            {formatCurrency(conflict.savings)}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <MapPin className="w-3 h-3 text-diya-text-muted flex-shrink-0" />
          <span className="text-diya-text-muted">Location:</span>
          <span className="truncate">{conflict.works[0]?.location.streetName}, {conflict.works[0]?.location.ward}</span>
        </div>
      </div>

      {/* Reasoning */}
      <div className="px-4 py-3">
        <span className="text-[10px] text-diya-text-muted uppercase tracking-wider block mb-1.5">
          AI Reasoning
        </span>
        <p className="text-xs text-diya-text-secondary leading-relaxed line-clamp-4">
          {conflict.reasoningTrace}
        </p>
      </div>

      {/* Actions */}
      <div className="px-4 py-3 border-t border-diya-border flex gap-2">
        <button className="btn-primary flex-1 text-xs">Resolve</button>
        <button className="btn-secondary text-xs">Dismiss</button>
      </div>
    </div>
  );
}
