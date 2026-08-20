'use client';

import { useState } from 'react';
import {
  Bot,
  Brain,
  Shield,
  ShieldAlert,
  FileText,
  Activity,
  Clock,
  ChevronRight,
  X,
  Cpu,
} from 'lucide-react';
import { agentActivities, reasoningTraces, departments } from '@/lib/mock-data';
import { cn, formatDuration, timeAgo, getStatusColor, getStatusBg } from '@/lib/utils';
import type { ReasoningTrace } from '@/types';

const agentTypeIcons: Record<string, any> = {
  department: Bot,
  coordinator: Brain,
  notice: FileText,
};

export default function AgentsPage() {
  const [selectedTrace, setSelectedTrace] = useState<ReasoningTrace | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>('all');

  const filteredActivities = agentActivities
    .filter((a) => typeFilter === 'all' || a.agentType === typeFilter)
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  const handleViewTrace = (traceId: string) => {
    const trace = reasoningTraces.find((t) => t.id === traceId);
    if (trace) setSelectedTrace(trace);
  };

  return (
    <div className="h-full flex flex-col lg:flex-row">
      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <div className="px-4 sm:px-6 pt-4 sm:pt-6 pb-3 sm:pb-4 flex-shrink-0">
          <div className="mb-4">
            <h1 className="page-title">Agent Observability</h1>
            <p className="page-subtitle">
              Real-time agent activity feed, reasoning traces, and governance events
            </p>
          </div>

          {/* Agent status cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
            <div className="card animate-fade-in">
              <div className="card-body">
                <div className="flex items-center gap-2 mb-2 sm:mb-3">
                  <Bot className="w-4 h-4 text-diya-text-secondary" />
                  <span className="text-xs font-medium">Department Agents</span>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xl sm:text-2xl font-light">4</span>
                    <span className="text-xs text-diya-text-muted ml-1">active</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {departments.map((d) => (
                      <div
                        key={d.id}
                        className={cn(
                          'w-2 h-2 rounded-full',
                          d.agentStatus === 'online' ? 'bg-diya-resolved' : 'bg-diya-pending'
                        )}
                        title={`${d.shortName}: ${d.agentStatus}`}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="card animate-fade-in">
              <div className="card-body">
                <div className="flex items-center gap-2 mb-2 sm:mb-3">
                  <Brain className="w-4 h-4 text-diya-text-secondary" />
                  <span className="text-xs font-medium">Coordinator Agent</span>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xl sm:text-2xl font-light">1</span>
                    <span className="text-xs text-diya-text-muted ml-1">active</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="status-dot status-dot-online" />
                    <span className="text-[10px] text-diya-text-muted">online</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="card animate-fade-in">
              <div className="card-body">
                <div className="flex items-center gap-2 mb-2 sm:mb-3">
                  <FileText className="w-4 h-4 text-diya-text-secondary" />
                  <span className="text-xs font-medium">Citizen Notice Agent</span>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xl sm:text-2xl font-light">1</span>
                    <span className="text-xs text-diya-text-muted ml-1">active</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="status-dot status-dot-online" />
                    <span className="text-[10px] text-diya-text-muted">online</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Filter tabs */}
          <div className="flex items-center gap-0.5 bg-diya-card border border-diya-border rounded-lg p-0.5 w-fit">
            {['all', 'department', 'coordinator', 'notice'].map((type) => (
              <button
                key={type}
                onClick={() => setTypeFilter(type)}
                className={cn(
                  'px-2.5 sm:px-3 py-1.5 text-xs rounded-md transition-colors duration-150 capitalize',
                  typeFilter === type
                    ? 'bg-white/10 text-white font-medium'
                    : 'text-diya-text-muted hover:text-diya-text'
                )}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        {/* Activity feed */}
        <div className="flex-1 overflow-y-auto px-4 sm:px-6 pb-4 sm:pb-6">
          <div className="space-y-0.5">
            {filteredActivities.map((activity) => {
              const Icon = agentTypeIcons[activity.agentType] || Bot;
              return (
                <div
                  key={activity.id}
                  className="group flex items-start gap-3 px-3 sm:px-4 py-3 rounded-lg hover:bg-diya-card/50 transition-colors duration-150"
                >
                  <div className="flex flex-col items-center pt-1 flex-shrink-0">
                    <div
                      className={cn(
                        'w-7 h-7 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center',
                        activity.status === 'blocked'
                          ? 'bg-diya-conflict-dim'
                          : activity.status === 'success'
                          ? 'bg-diya-surface'
                          : 'bg-diya-pending-dim'
                      )}
                    >
                      {activity.status === 'blocked' ? (
                        <ShieldAlert className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-diya-conflict" />
                      ) : (
                        <Icon className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-diya-text-secondary" />
                      )}
                    </div>
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                      <span className="text-xs font-medium">{activity.agentName}</span>
                      <span className={cn('badge', getStatusBg(activity.status), getStatusColor(activity.status))}>
                        {activity.status}
                      </span>
                    </div>
                    <p className="text-xs text-diya-text-muted mb-0.5 font-medium">
                      {activity.action}
                    </p>
                    <p className="text-xs text-diya-text-secondary leading-relaxed">
                      {activity.detail}
                    </p>
                    <div className="flex items-center gap-3 mt-1.5 flex-wrap">
                      <span className="text-[10px] text-diya-text-muted flex items-center gap-1">
                        <Clock className="w-2.5 h-2.5" />
                        {timeAgo(activity.timestamp)}
                      </span>
                      {activity.duration && (
                        <span className="text-[10px] text-diya-text-muted flex items-center gap-1">
                          <Activity className="w-2.5 h-2.5" />
                          {formatDuration(activity.duration)}
                        </span>
                      )}
                      {activity.traceId && (
                        <button
                          onClick={() => handleViewTrace(activity.traceId!)}
                          className="text-[10px] text-white/60 hover:text-white flex items-center gap-1 transition-colors"
                        >
                          <Brain className="w-2.5 h-2.5" />
                          View Trace
                          <ChevronRight className="w-2.5 h-2.5" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Reasoning trace panel */}
      {selectedTrace && (
        <div className="w-full lg:w-[400px] xl:w-[420px] border-t lg:border-t-0 lg:border-l border-diya-border bg-diya-surface overflow-y-auto flex-shrink-0 max-h-[50vh] lg:max-h-none animate-fade-in">
          <div className="sticky top-0 bg-diya-surface z-10 px-4 sm:px-5 py-3 sm:py-4 border-b border-diya-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-diya-text-secondary" />
              <h3 className="text-sm font-medium">Reasoning Trace</h3>
            </div>
            <button
              onClick={() => setSelectedTrace(null)}
              className="w-6 h-6 rounded-md hover:bg-diya-card flex items-center justify-center"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="p-4 sm:p-5">
            {/* Trace header */}
            <div className="mb-5">
              <span className="font-mono text-sm">{selectedTrace.id}</span>
              <p className="text-xs text-diya-text-muted mt-0.5">
                {selectedTrace.agentName} &middot; Conflict {selectedTrace.conflictId}
              </p>
              <div className="flex items-center gap-3 mt-2 text-xs text-diya-text-muted">
                <span className="flex items-center gap-1">
                  <Cpu className="w-3 h-3" />
                  {selectedTrace.steps.length} steps
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatDuration(selectedTrace.totalDuration)}
                </span>
              </div>
            </div>

            {/* Steps */}
            <div className="space-y-0">
              {selectedTrace.steps.map((step, i) => (
                <div key={step.step} className="relative pl-6 pb-5">
                  {i < selectedTrace.steps.length - 1 && (
                    <div className="absolute left-[9px] top-6 bottom-0 w-px bg-diya-border" />
                  )}
                  <div className="absolute left-0 top-1 w-[18px] h-[18px] rounded-full bg-diya-card border border-diya-border flex items-center justify-center">
                    <span className="text-[9px] font-mono text-diya-text-muted">{step.step}</span>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium">{step.action}</span>
                      <span className="text-[10px] text-diya-text-muted">{formatDuration(step.duration)}</span>
                    </div>
                    <div className="card mb-2">
                      <div className="px-3 py-2">
                        <span className="text-[10px] text-diya-text-muted uppercase tracking-wider block mb-1">Reasoning</span>
                        <p className="text-[11px] text-diya-text-secondary leading-relaxed">{step.reasoning}</p>
                      </div>
                    </div>
                    <div className="card">
                      <div className="px-3 py-2">
                        <span className="text-[10px] text-diya-text-muted uppercase tracking-wider block mb-1">Result</span>
                        <p className="text-[11px] text-diya-resolved leading-relaxed">{step.result}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Outcome */}
            <div className="mt-4 card">
              <div className="px-4 py-3">
                <span className="data-label block mb-1">Final Outcome</span>
                <p className="text-xs text-diya-text-secondary leading-relaxed">{selectedTrace.outcome}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
