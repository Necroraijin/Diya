'use client';

import { useState } from 'react';
import {
  Route,
  Droplets,
  Wifi,
  Waves,
  Shield,
  Eye,
  EyeOff,
  ChevronRight,
  Clock,
  MapPin,
  IndianRupee,
} from 'lucide-react';
import { useDepartments, usePlannedWorks } from '@/lib/live';
import { cn, formatDate, formatCurrency, getStatusColor, getStatusBg } from '@/lib/utils';

const iconMap: Record<string, any> = {
  road: Route,
  droplets: Droplets,
  wifi: Wifi,
  waves: Waves,
};

export default function DepartmentsPage() {
  const [selectedDept, setSelectedDept] = useState<string | null>(null);
  const { data: departments } = useDepartments();
  const { data: plannedWorks } = usePlannedWorks();

  return (
    <div className="page-container">
      <div className="mb-5 sm:mb-6">
        <h1 className="page-title">Departments</h1>
        <p className="page-subtitle">
          Municipal department agents, identity scoping, and planned infrastructure works
        </p>
      </div>

      {/* Department Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4 mb-6">
        {departments.map((dept: any) => {
          const Icon = iconMap[dept.icon] || Route;
          const deptWorks = plannedWorks.filter((w: any) => w.deptId === dept.id);
          const conflictedWorks = deptWorks.filter((w: any) => w.status === 'conflicted');
          const isSelected = selectedDept === dept.id;

          return (
            <div
              key={dept.id}
              onClick={() => setSelectedDept(isSelected ? null : dept.id)}
              className={cn(
                'card cursor-pointer transition-colors duration-150 animate-fade-in',
                isSelected ? 'border-white/20' : 'hover:border-diya-border-light'
              )}
            >
              <div className="card-body">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-lg bg-diya-surface border border-diya-border flex items-center justify-center flex-shrink-0">
                      <Icon className="w-4 h-4 sm:w-5 sm:h-5 text-diya-text-secondary" strokeWidth={1.5} />
                    </div>
                    <div className="min-w-0">
                      <h3 className="text-xs sm:text-sm font-medium truncate">{dept.name}</h3>
                      <p className="text-[10px] sm:text-xs text-diya-text-muted mt-0.5 truncate">
                        Agent: {dept.agentIdentityId}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
                    <div
                      className={cn(
                        'status-dot',
                        dept.agentStatus === 'online' && 'status-dot-online',
                        dept.agentStatus === 'offline' && 'status-dot-offline',
                        dept.agentStatus === 'processing' && 'status-dot-processing'
                      )}
                    />
                    <span className="text-[10px] text-diya-text-muted capitalize">
                      {dept.agentStatus}
                    </span>
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-2 sm:gap-3 mb-3 sm:mb-4">
                  <div className="bg-diya-surface rounded-md p-2 sm:p-3 text-center">
                    <div className="text-lg sm:text-xl font-light">{deptWorks.length}</div>
                    <div className="text-[9px] sm:text-[10px] text-diya-text-muted uppercase tracking-wider mt-0.5">Works</div>
                  </div>
                  <div className="bg-diya-surface rounded-md p-2 sm:p-3 text-center">
                    <div className={cn('text-lg sm:text-xl font-light', conflictedWorks.length > 0 && 'text-diya-conflict')}>
                      {conflictedWorks.length}
                    </div>
                    <div className="text-[9px] sm:text-[10px] text-diya-text-muted uppercase tracking-wider mt-0.5">Conflicts</div>
                  </div>
                  <div className="bg-diya-surface rounded-md p-2 sm:p-3 text-center">
                    <div className="text-lg sm:text-xl font-light">
                      {formatCurrency(deptWorks.reduce((sum, w) => sum + w.budget, 0))}
                    </div>
                    <div className="text-[9px] sm:text-[10px] text-diya-text-muted uppercase tracking-wider mt-0.5">Budget</div>
                  </div>
                </div>

                {/* Identity scope */}
                <div className="flex items-center gap-2 px-2 sm:px-3 py-2 bg-diya-surface rounded-md">
                  <Shield className="w-3.5 h-3.5 text-diya-text-muted flex-shrink-0" />
                  <span className="text-[10px] text-diya-text-muted flex-shrink-0">Scope:</span>
                  <span className="text-[10px] font-mono text-diya-text-secondary truncate">
                    departments/{dept.id}/planned_works/*
                  </span>
                  <div className="ml-auto flex items-center gap-1 flex-shrink-0">
                    <Eye className="w-3 h-3 text-diya-resolved" />
                    <span className="text-[10px] text-diya-resolved">read</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 px-2 sm:px-3 py-2 bg-diya-conflict-dim/50 rounded-md mt-1">
                  <EyeOff className="w-3.5 h-3.5 text-diya-conflict/70 flex-shrink-0" />
                  <span className="text-[10px] text-diya-conflict/70">
                    Cross-department access: DENIED
                  </span>
                </div>
              </div>

              {/* Expand indicator */}
              <div className="px-4 sm:px-5 py-2 border-t border-diya-border flex items-center justify-between">
                <span className="text-[10px] text-diya-text-muted">
                  {isSelected ? 'Hide works' : 'View planned works'}
                </span>
                <ChevronRight
                  className={cn(
                    'w-3 h-3 text-diya-text-muted transition-transform duration-200',
                    isSelected && 'rotate-90'
                  )}
                />
              </div>

              {/* Expanded works list */}
              {isSelected && (
                <div className="border-t border-diya-border">
                  {deptWorks.map((work) => (
                    <div
                      key={work.id}
                      className="px-4 sm:px-5 py-3 border-b border-diya-border last:border-0 hover:bg-diya-card-hover/50 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-1 flex-wrap gap-1">
                        <span className="text-xs font-medium">{work.title}</span>
                        <span className={cn('badge', getStatusBg(work.status), getStatusColor(work.status))}>
                          {work.status}
                        </span>
                      </div>
                      <p className="text-[10px] text-diya-text-muted line-clamp-1 mb-1.5">
                        {work.description}
                      </p>
                      <div className="flex items-center gap-2 sm:gap-3 text-[10px] text-diya-text-muted flex-wrap">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-2.5 h-2.5" />
                          {work.location.streetName}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-2.5 h-2.5" />
                          {formatDate(work.startDate)} — {formatDate(work.endDate)}
                        </span>
                        <span className="flex items-center gap-1">
                          <IndianRupee className="w-2.5 h-2.5" />
                          {formatCurrency(work.budget)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
