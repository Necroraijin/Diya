'use client';

import { usePathname } from 'next/navigation';
import {
  Search,
  Bell,
  Activity,
  ChevronRight,
} from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { useConnection } from '@/lib/live';

const pageTitles: Record<string, { title: string; breadcrumb: string[] }> = {
  '/dashboard': { title: 'Dashboard', breadcrumb: ['DIYA', 'Dashboard'] },
  '/map': { title: 'City Mesh', breadcrumb: ['DIYA', 'City Mesh'] },
  '/conflicts': { title: 'Conflicts', breadcrumb: ['DIYA', 'Conflicts'] },
  '/departments': { title: 'Departments', breadcrumb: ['DIYA', 'Departments'] },
  '/notices': { title: 'Citizen Notices', breadcrumb: ['DIYA', 'Notices'] },
  '/agents': { title: 'Agent Activity', breadcrumb: ['DIYA', 'Agents'] },
};

export default function TopBar() {
  const pathname = usePathname();
  const [searchOpen, setSearchOpen] = useState(false);
  const pageInfo = pageTitles[pathname || '/dashboard'] || pageTitles['/dashboard'];
  const connection = useConnection();

  // Three states, not two: "we have not checked yet" is not the same claim as
  // "the gateway is down", and showing DEMO for the first few hundred
  // milliseconds of every page load would be a lie in the other direction.
  const status = {
    live: { label: 'Live — API Gateway', dot: 'bg-diya-resolved status-dot-online' },
    demo: { label: 'Demo data — gateway offline', dot: 'bg-diya-warning' },
    loading: { label: 'Connecting…', dot: 'bg-diya-text-muted' },
  }[connection];

  return (
    <header className="h-12 sm:h-14 bg-diya-surface/50 backdrop-blur-md border-b border-diya-border flex items-center justify-between px-4 sm:px-6 z-40 flex-shrink-0">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2">
        {pageInfo.breadcrumb.map((crumb, i) => (
          <div key={i} className="flex items-center gap-2">
            {i > 0 && <ChevronRight className="w-3 h-3 text-diya-text-muted" />}
            <span
              className={cn(
                'text-sm',
                i === pageInfo.breadcrumb.length - 1
                  ? 'font-medium text-diya-text'
                  : 'text-diya-text-muted hidden sm:inline'
              )}
            >
              {crumb}
            </span>
          </div>
        ))}
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-1.5 sm:gap-2">
        {/* System status - hidden on mobile */}
        <div
          className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-diya-card border border-diya-border mr-1"
          title={status.label}
        >
          <div className={cn('w-1.5 h-1.5 rounded-full', status.dot)} />
          <span className="text-xs text-diya-text-muted">{status.label}</span>
          <Activity className="w-3 h-3 text-diya-text-muted" />
        </div>

        {/* Search */}
        <div className="relative">
          <button
            onClick={() => setSearchOpen(!searchOpen)}
            className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-diya-card transition-colors"
          >
            <Search className="w-4 h-4 text-diya-text-muted" />
          </button>
          {searchOpen && (
            <div className="absolute right-0 top-full mt-1 z-50">
              <input
                className="input-field w-64 sm:w-80 text-xs shadow-xl"
                placeholder="Search conflicts, works, agents..."
                autoFocus
                onBlur={() => setSearchOpen(false)}
              />
            </div>
          )}
        </div>

        {/* Notifications */}
        <button className="relative w-9 h-9 flex items-center justify-center rounded-lg hover:bg-diya-card transition-colors">
          <Bell className="w-4 h-4 text-diya-text-muted" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-diya-conflict rounded-full" />
        </button>

        {/* User avatar */}
        <div className="w-8 h-8 rounded-full bg-diya-border flex items-center justify-center ml-1">
          <span className="text-xs font-medium">S</span>
        </div>
      </div>
    </header>
  );
}
