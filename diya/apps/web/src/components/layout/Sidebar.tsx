'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Map,
  AlertTriangle,
  Building2,
  FileText,
  Bot,
  Shield,
  ChevronLeft,
  ChevronRight,
  Hexagon,
  Settings,
  HelpCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/map', label: 'City Mesh', icon: Map },
  { href: '/conflicts', label: 'Conflicts', icon: AlertTriangle, badge: 3 },
  { href: '/departments', label: 'Departments', icon: Building2 },
  { href: '/notices', label: 'Notices', icon: FileText },
  { href: '/agents', label: 'Agents', icon: Bot },
  { href: '/governance', label: 'Governance', icon: Shield },
];

const bottomItems = [
  { href: '/settings', label: 'Settings', icon: Settings },
  { href: '/help', label: 'Help', icon: HelpCircle },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  // Auto-collapse on small screens
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) setCollapsed(true);
      else setCollapsed(false);
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <aside
      className={cn(
        'h-screen bg-diya-surface border-r border-diya-border flex flex-col relative z-50 transition-[width] duration-300 ease-in-out flex-shrink-0',
        collapsed ? 'w-16' : 'w-[220px] xl:w-[240px]'
      )}
    >
      {/* Logo */}
      <div className="h-14 flex items-center px-4 border-b border-diya-border">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-8 h-8 flex items-center justify-center flex-shrink-0">
            <Hexagon className="w-6 h-6 text-white" strokeWidth={1.5} />
          </div>
          {!collapsed && (
            <div className="flex flex-col animate-fade-in">
              <span className="text-sm font-semibold tracking-widest whitespace-nowrap">DIYA</span>
              <span className="text-[10px] text-diya-text-muted tracking-wider whitespace-nowrap">INFRASTRUCTURE</span>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.label : undefined}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors duration-150 group relative',
                isActive
                  ? 'bg-white/10 text-white'
                  : 'text-diya-text-muted hover:text-diya-text hover:bg-diya-card'
              )}
            >
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-white rounded-r" />
              )}
              <item.icon className="w-[18px] h-[18px] flex-shrink-0" strokeWidth={1.5} />
              {!collapsed && (
                <span className="font-medium truncate">{item.label}</span>
              )}
              {isActive && !collapsed && item.badge && (
                <span className="ml-auto bg-diya-conflict text-white text-[10px] font-bold w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom items */}
      <div className="px-2 pb-2 space-y-0.5 border-t border-diya-border pt-2">
        {bottomItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            title={collapsed ? item.label : undefined}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-diya-text-muted hover:text-diya-text hover:bg-diya-card transition-colors duration-150"
          >
            <item.icon className="w-[18px] h-[18px] flex-shrink-0" strokeWidth={1.5} />
            {!collapsed && <span className="truncate">{item.label}</span>}
          </Link>
        ))}
      </div>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-20 w-6 h-6 bg-diya-card border border-diya-border rounded-full flex items-center justify-center hover:bg-diya-card-hover transition-colors z-50 hidden lg:flex"
      >
        {collapsed ? (
          <ChevronRight className="w-3 h-3" />
        ) : (
          <ChevronLeft className="w-3 h-3" />
        )}
      </button>
    </aside>
  );
}
