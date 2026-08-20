import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

export function formatDateTime(dateString: string): string {
  return new Date(dateString).toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatCurrency(amount: number): string {
  if (amount >= 10000000) {
    return `${(amount / 10000000).toFixed(1)} Cr`;
  }
  if (amount >= 100000) {
    return `${(amount / 100000).toFixed(1)} L`;
  }
  return new Intl.NumberFormat('en-IN').format(amount);
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'detected':
    case 'conflict':
    case 'conflicted':
    case 'critical':
    case 'error':
    case 'blocked':
      return 'text-diya-conflict';
    case 'resolved':
    case 'completed':
    case 'success':
    case 'online':
      return 'text-diya-resolved';
    case 'pending':
    case 'planned':
    case 'processing':
    case 'in-progress':
    case 'medium':
    case 'high':
      return 'text-diya-pending';
    case 'dismissed':
    case 'low':
    case 'offline':
    case 'draft':
      return 'text-diya-text-muted';
    default:
      return 'text-diya-text-secondary';
  }
}

export function getStatusBg(status: string): string {
  switch (status) {
    case 'detected':
    case 'conflict':
    case 'conflicted':
    case 'critical':
    case 'error':
    case 'blocked':
      return 'bg-diya-conflict-dim';
    case 'resolved':
    case 'completed':
    case 'success':
    case 'online':
      return 'bg-diya-resolved-dim';
    case 'pending':
    case 'planned':
    case 'processing':
    case 'in-progress':
    case 'medium':
    case 'high':
      return 'bg-diya-pending-dim';
    default:
      return 'bg-diya-card';
  }
}

export function timeAgo(dateString: string): string {
  const now = new Date();
  const date = new Date(dateString);
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}
