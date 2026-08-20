'use client';

import { AlertTriangle, CheckCircle2, Building2, Wrench, IndianRupee, FileText } from 'lucide-react';
import MetricCard from '@/components/dashboard/MetricCard';
import ConflictTimeline from '@/components/dashboard/ConflictTimeline';
import LiveFeed from '@/components/dashboard/LiveFeed';
import DepartmentGrid from '@/components/dashboard/DepartmentGrid';
import { dashboardMetrics } from '@/lib/mock-data';
import { formatCurrency } from '@/lib/utils';

export default function DashboardPage() {
  return (
    <div className="page-container">
      <div className="mb-5 sm:mb-6">
        <h1 className="page-title">Command Center</h1>
        <p className="page-subtitle">
          Real-time infrastructure conflict monitoring across all municipal departments
        </p>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3 sm:gap-4 mb-5 sm:mb-6">
        <MetricCard
          title="Active Conflicts"
          value={dashboardMetrics.totalConflicts - dashboardMetrics.resolvedConflicts}
          icon={AlertTriangle}
          trend={{ value: 33, label: 'this week' }}
          accentColor="bg-diya-conflict-dim border-diya-conflict/20"
        />
        <MetricCard
          title="Resolved"
          value={dashboardMetrics.resolvedConflicts}
          icon={CheckCircle2}
          accentColor="bg-diya-resolved-dim border-diya-resolved/20"
        />
        <MetricCard
          title="Departments"
          value={dashboardMetrics.departments}
          icon={Building2}
        />
        <MetricCard
          title="Planned Works"
          value={dashboardMetrics.activeWorks}
          icon={Wrench}
        />
        <MetricCard
          title="Est. Savings"
          value={formatCurrency(dashboardMetrics.estimatedSavings)}
          icon={IndianRupee}
          subtitle="From consolidated work windows"
          accentColor="bg-diya-resolved-dim border-diya-resolved/20"
        />
        <MetricCard
          title="Notices Issued"
          value={dashboardMetrics.citizenNotices}
          icon={FileText}
        />
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 sm:gap-4">
        <div className="lg:col-span-2 space-y-3 sm:space-y-4">
          <ConflictTimeline />
          <DepartmentGrid />
        </div>
        <div>
          <LiveFeed />
        </div>
      </div>
    </div>
  );
}
