'use client';

import { useState } from 'react';
import {
  AlertTriangle,
  Search,
  Clock,
  MapPin,
  IndianRupee,
  Brain,
  X,
  CheckCircle2,
  XCircle,
  ArrowRight,
} from 'lucide-react';
import { conflicts } from '@/lib/mock-data';
import { cn, formatDate, formatCurrency, getStatusColor, getStatusBg, timeAgo } from '@/lib/utils';
import type { Conflict } from '@/types';

export default function ConflictsPage() {
  const [selectedConflict, setSelectedConflict] = useState<Conflict | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredConflicts = conflicts.filter((c) => {
    if (statusFilter !== 'all' && c.status !== statusFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        c.id.toLowerCase().includes(q) ||
        c.works.some((w) => w.title.toLowerCase().includes(q) || w.location.streetName.toLowerCase().includes(q))
      );
    }
    return true;
  });

  return (
    <div className="h-full flex flex-col lg:flex-row">
      {/* Main list */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <div className="px-4 sm:px-6 pt-4 sm:pt-6 pb-3 sm:pb-4 flex-shrink-0">
          <div className="flex items-start sm:items-center justify-between mb-4 flex-col sm:flex-row gap-2">
            <div>
              <h1 className="page-title">Conflict Detection</h1>
              <p className="page-subtitle">
                Cross-department infrastructure conflicts detected by the Coordinator Agent
              </p>
            </div>
            <span className="text-xs text-diya-text-muted flex-shrink-0">
              {filteredConflicts.length} conflicts
            </span>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-3 flex-wrap">
            <div className="relative flex-1 min-w-[200px] max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-diya-text-muted" />
              <input
                type="text"
                placeholder="Search by ID, location, or work title..."
                className="input-field pl-9"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-0.5 bg-diya-card border border-diya-border rounded-lg p-0.5">
              {['all', 'detected', 'resolved', 'dismissed'].map((status) => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  className={cn(
                    'px-2.5 sm:px-3 py-1.5 text-xs rounded-md transition-colors duration-150 capitalize',
                    statusFilter === status
                      ? 'bg-white/10 text-white font-medium'
                      : 'text-diya-text-muted hover:text-diya-text'
                  )}
                >
                  {status}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Conflict list */}
        <div className="flex-1 overflow-y-auto px-4 sm:px-6 pb-4 sm:pb-6">
          <div className="space-y-3">
            {filteredConflicts.map((conflict) => (
              <div
                key={conflict.id}
                onClick={() => setSelectedConflict(conflict)}
                className={cn(
                  'card cursor-pointer transition-colors duration-150 animate-fade-in',
                  selectedConflict?.id === conflict.id
                    ? 'border-white/20'
                    : 'hover:border-diya-border-light'
                )}
              >
                <div className="card-body">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div
                        className={cn(
                          'w-8 h-8 sm:w-9 sm:h-9 rounded-lg flex items-center justify-center flex-shrink-0',
                          getStatusBg(conflict.severity)
                        )}
                      >
                        <AlertTriangle
                          className={cn('w-4 h-4', getStatusColor(conflict.severity))}
                        />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-medium font-mono">{conflict.id}</span>
                          <span className={cn('badge', getStatusBg(conflict.status), getStatusColor(conflict.status))}>
                            {conflict.status}
                          </span>
                          <span className={cn('badge', getStatusBg(conflict.severity), getStatusColor(conflict.severity))}>
                            {conflict.severity}
                          </span>
                        </div>
                        <p className="text-xs text-diya-text-muted mt-0.5">
                          {conflict.works.length} works &middot; {conflict.overlapType} overlap &middot; {conflict.city}
                        </p>
                      </div>
                    </div>
                    <span className="text-[10px] text-diya-text-muted flex-shrink-0 ml-2">
                      {timeAgo(conflict.detectedAt)}
                    </span>
                  </div>

                  {/* Affected works summary */}
                  <div className="flex flex-wrap gap-1.5 sm:gap-2 mb-3">
                    {conflict.works.map((work) => (
                      <div
                        key={work.id}
                        className="flex items-center gap-1.5 px-2 py-1 bg-diya-surface rounded text-[11px]"
                      >
                        <div
                          className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                          style={{ backgroundColor: work.status === 'conflicted' ? '#ef4444' : '#666' }}
                        />
                        <span className="text-diya-text-secondary">{work.deptName}</span>
                        <span className="text-diya-text-muted hidden sm:inline">&middot;</span>
                        <span className="text-diya-text-muted truncate max-w-[120px] hidden sm:inline">
                          {work.title}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Footer */}
                  <div className="flex items-center gap-3 sm:gap-4 text-xs text-diya-text-muted flex-wrap">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {conflict.works[0]?.location.streetName}
                    </span>
                    <span className="flex items-center gap-1 hidden sm:flex">
                      <Clock className="w-3 h-3" />
                      {formatDate(conflict.proposedWindow.start)} — {formatDate(conflict.proposedWindow.end)}
                    </span>
                    {conflict.savings > 0 && (
                      <span className="flex items-center gap-1 text-diya-resolved">
                        <IndianRupee className="w-3 h-3" />
                        {formatCurrency(conflict.savings)} savings
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Detail panel */}
      {selectedConflict && (
        <div className="w-full lg:w-96 border-t lg:border-t-0 lg:border-l border-diya-border bg-diya-surface overflow-y-auto flex-shrink-0 max-h-[50vh] lg:max-h-none animate-fade-in">
          <div className="sticky top-0 bg-diya-surface z-10 px-4 sm:px-5 py-3 sm:py-4 border-b border-diya-border flex items-center justify-between">
            <h3 className="text-sm font-medium">Conflict Detail</h3>
            <button
              onClick={() => setSelectedConflict(null)}
              className="w-6 h-6 rounded-md hover:bg-diya-card flex items-center justify-center"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="p-4 sm:p-5 space-y-4 sm:space-y-5">
            {/* ID & Status */}
            <div>
              <span className="font-mono text-lg">{selectedConflict.id}</span>
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                <span className={cn('badge', getStatusBg(selectedConflict.status), getStatusColor(selectedConflict.status))}>
                  {selectedConflict.status}
                </span>
                <span className={cn('badge', getStatusBg(selectedConflict.severity), getStatusColor(selectedConflict.severity))}>
                  {selectedConflict.severity}
                </span>
                <span className="badge bg-diya-card text-diya-text-secondary">
                  {selectedConflict.overlapType}
                </span>
              </div>
            </div>

            {/* Proposed Window */}
            <div className="card">
              <div className="card-body">
                <span className="data-label block mb-2">Proposed Consolidated Window</span>
                <div className="flex items-center gap-2 text-sm flex-wrap">
                  <span>{formatDate(selectedConflict.proposedWindow.start)}</span>
                  <ArrowRight className="w-3 h-3 text-diya-text-muted" />
                  <span>{formatDate(selectedConflict.proposedWindow.end)}</span>
                </div>
                {selectedConflict.savings > 0 && (
                  <div className="mt-2 flex items-center gap-1.5 text-sm text-diya-resolved">
                    <IndianRupee className="w-3.5 h-3.5" />
                    <span className="font-medium">{formatCurrency(selectedConflict.savings)}</span>
                    <span className="text-xs text-diya-text-muted">estimated savings</span>
                  </div>
                )}
              </div>
            </div>

            {/* Affected Works */}
            <div>
              <span className="data-label block mb-3">Affected Works</span>
              <div className="space-y-2">
                {selectedConflict.works.map((work) => (
                  <div key={work.id} className="card">
                    <div className="px-3 sm:px-4 py-2.5 sm:py-3">
                      <span className="text-xs font-medium block mb-1">{work.title}</span>
                      <div className="flex items-center gap-2 sm:gap-3 text-[10px] text-diya-text-muted flex-wrap">
                        <span>{work.deptName}</span>
                        <span>{work.workType}</span>
                        <span>{formatCurrency(work.budget)}</span>
                      </div>
                      <div className="text-[10px] text-diya-text-muted mt-1">
                        {formatDate(work.startDate)} — {formatDate(work.endDate)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Reasoning */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Brain className="w-3.5 h-3.5 text-diya-text-muted" />
                <span className="data-label">AI Reasoning Trace</span>
              </div>
              <div className="card">
                <div className="px-3 sm:px-4 py-2.5 sm:py-3">
                  <p className="text-xs text-diya-text-secondary leading-relaxed">
                    {selectedConflict.reasoningTrace}
                  </p>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-2">
              <button className="btn-primary flex-1 flex items-center justify-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Resolve
              </button>
              <button className="btn-secondary flex items-center justify-center gap-2">
                <XCircle className="w-3.5 h-3.5" />
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
