'use client';

import { Route, Droplets, Wifi, Waves } from 'lucide-react';
import { useDepartments } from '@/lib/live';
import { cn } from '@/lib/utils';

const iconMap: Record<string, any> = {
  road: Route,
  droplets: Droplets,
  wifi: Wifi,
  waves: Waves,
};

export default function DepartmentGrid() {
  const { data: departments } = useDepartments();

  return (
    <div className="card animate-slide-up">
      <div className="card-header">
        <h3 className="text-sm font-medium">Department Status</h3>
        <span className="text-xs text-diya-text-muted">{departments.length} active</span>
      </div>
      <div className="grid grid-cols-2 gap-px bg-diya-border">
        {departments.map((dept: any) => {
          const Icon = iconMap[dept.icon] || Route;
          return (
            <div
              key={dept.id}
              className="bg-diya-card p-3 sm:p-4 hover:bg-diya-card-hover transition-colors"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Icon className="w-4 h-4 text-diya-text-secondary" strokeWidth={1.5} />
                  <span className="text-xs font-medium">{dept.shortName}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div
                    className={cn(
                      'status-dot',
                      dept.agentStatus === 'online' && 'status-dot-online',
                      dept.agentStatus === 'offline' && 'status-dot-offline',
                      dept.agentStatus === 'processing' && 'status-dot-processing'
                    )}
                  />
                  <span className="text-[10px] text-diya-text-muted capitalize hidden sm:inline">
                    {dept.agentStatus}
                  </span>
                </div>
              </div>
              <div className="text-xl sm:text-2xl font-light mb-1">{dept.activeWorks}</div>
              <div className="text-[10px] text-diya-text-muted uppercase tracking-wider">
                Active Works
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
