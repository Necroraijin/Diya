'use client';

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { dashboardMetrics } from '@/lib/mock-data';

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload) return null;
  return (
    <div className="bg-diya-card border border-diya-border rounded-lg px-3 py-2 shadow-xl">
      <p className="text-xs text-diya-text-muted mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} className="text-xs">
          <span className="text-diya-text-muted">{entry.name}: </span>
          <span className="font-medium">{entry.value}</span>
        </p>
      ))}
    </div>
  );
};

export default function ConflictTimeline() {
  return (
    <div className="card animate-slide-up">
      <div className="card-header">
        <div>
          <h3 className="text-sm font-medium">Conflict Trend</h3>
          <p className="text-xs text-diya-text-muted mt-0.5">Last 7 days</p>
        </div>
        <div className="flex gap-3 sm:gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-white/40" />
            <span className="text-[10px] sm:text-xs text-diya-text-muted">Detected</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-white" />
            <span className="text-[10px] sm:text-xs text-diya-text-muted">Resolved</span>
          </div>
        </div>
      </div>
      <div className="p-3 sm:p-4 h-[180px] sm:h-[220px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={dashboardMetrics.conflictTrend}>
            <defs>
              <linearGradient id="gradDetected" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="rgba(255,255,255,0.15)" />
                <stop offset="100%" stopColor="rgba(255,255,255,0)" />
              </linearGradient>
              <linearGradient id="gradResolved" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="rgba(255,255,255,0.3)" />
                <stop offset="100%" stopColor="rgba(255,255,255,0)" />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis
              dataKey="date"
              tick={{ fill: '#666', fontSize: 11 }}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              tickLine={false}
              tickFormatter={(val) => val.split('-').slice(1).join('/')}
            />
            <YAxis
              tick={{ fill: '#666', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={25}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="detected"
              name="Detected"
              stroke="rgba(255,255,255,0.4)"
              fill="url(#gradDetected)"
              strokeWidth={1.5}
            />
            <Area
              type="monotone"
              dataKey="resolved"
              name="Resolved"
              stroke="rgba(255,255,255,0.9)"
              fill="url(#gradResolved)"
              strokeWidth={1.5}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
