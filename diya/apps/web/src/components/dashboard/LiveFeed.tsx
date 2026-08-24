'use client';

import {
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Bot,
  Brain,
  FileText,
  Shield,
} from 'lucide-react';
import { useAgentActivity } from '@/lib/live';
import { cn, timeAgo, getStatusColor, formatDuration } from '@/lib/utils';

const getActivityIcon = (action: string, status: string) => {
  if (status === 'blocked') return ShieldAlert;
  if (action.includes('Conflict Detection')) return AlertTriangle;
  if (action.includes('Resolution') || action.includes('Memory')) return Brain;
  if (action.includes('Notice')) return FileText;
  if (action.includes('Model Armor')) return Shield;
  return Bot;
};

export default function LiveFeed() {
  // Refetches on every agent.activity / armor.blocked SSE event, so this really
  // is live rather than a fixture named "live".
  const { data: activities } = useAgentActivity(50);
  const sortedActivities = [...activities].sort(
    (a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  return (
    <div className="card animate-slide-up">
      <div className="card-header">
        <div className="flex items-center gap-2">
          <div className="status-dot status-dot-online" />
          <h3 className="text-sm font-medium">Live Agent Feed</h3>
        </div>
        <span className="text-xs text-diya-text-muted">{sortedActivities.length} events</span>
      </div>
      <div className="overflow-y-auto max-h-[350px] lg:max-h-[450px]">
        {sortedActivities.map((activity: any) => {
          const Icon = getActivityIcon(activity.action, activity.status);
          return (
            <div
              key={activity.id}
              className="px-4 py-3 border-b border-diya-border hover:bg-diya-card-hover/50 transition-colors group"
            >
              <div className="flex items-start gap-3">
                <div
                  className={cn(
                    'w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5',
                    activity.status === 'blocked' || activity.status === 'error'
                      ? 'bg-diya-conflict-dim'
                      : 'bg-diya-surface'
                  )}
                >
                  <Icon className={cn('w-3.5 h-3.5', getStatusColor(activity.status))} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                    <span className="text-xs font-medium truncate">{activity.agentName}</span>
                    <span className="text-[10px] text-diya-text-muted">{activity.action}</span>
                  </div>
                  <p className="text-xs text-diya-text-secondary leading-relaxed line-clamp-2">
                    {activity.detail}
                  </p>
                  <div className="flex items-center gap-3 mt-1.5">
                    <span className="text-[10px] text-diya-text-muted">
                      {timeAgo(activity.timestamp)}
                    </span>
                    {activity.duration && (
                      <span className="text-[10px] text-diya-text-muted">
                        {formatDuration(activity.duration)}
                      </span>
                    )}
                    {activity.traceId && (
                      <span className="text-[10px] text-diya-info opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer hover:underline">
                        View Trace
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
