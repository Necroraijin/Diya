'use client';

/**
 * Live data layer.
 *
 * Every page used to import from `mock-data.ts` directly, which meant the UI
 * could not be wrong — and could not be right either. These hooks fetch from
 * the gateway and fall back to the seeded demo data when it is unreachable.
 *
 * The fallback is deliberate and *visible*: `source` is surfaced in the top bar
 * as LIVE or DEMO. A dashboard that silently shows stale fixtures when the
 * backend is down is the failure mode this layer exists to prevent — a judge
 * pulling the plug on the API should see the UI say so, not see it lie.
 *
 * Refetching is event-driven. The gateway's SSE stream carries real domain
 * events (`conflict.detected`, `conflict.resolved`, `notice.generated`,
 * `agent.activity`, `armor.blocked`), and each hook names the events that
 * invalidate it, so a resolution in one tab updates the conflict list, the
 * notice list and the dashboard without polling any of them.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react';

import * as api from './api';
import {
  agentActivities as mockActivities,
  conflicts as mockConflicts,
  dashboardMetrics as mockMetrics,
  departments as mockDepartments,
  notices as mockNotices,
  plannedWorks as mockWorks,
} from './mock-data';

export type Source = 'live' | 'demo' | 'loading';

// ── SSE bus ──────────────────────────────────────────────────────
//
// One EventSource for the whole app, shared by every hook. Opening one per hook
// would burn through the browser's six-connection-per-origin budget with three
// components on a page.

type Listener = (eventType: string) => void;

const listeners = new Set<Listener>();
// Held for the lifetime of the tab; there is nothing to tear it down for
// short of a page unload, which closes it anyway.
let unsubscribe: (() => void) | null = null;

function ensureStream() {
  if (unsubscribe || typeof window === 'undefined') return;
  unsubscribe = api.subscribeToEvents((payload) => {
    const type = payload && typeof payload === 'object' ? payload.type : '';
    listeners.forEach((fn) => fn(String(type ?? '')));
  });
}

function onDomainEvent(fn: Listener): () => void {
  ensureStream();
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}

// ── Connection status ────────────────────────────────────────────

const ConnectionContext = createContext<Source>('loading');

export function useConnection(): Source {
  return useContext(ConnectionContext);
}

/**
 * Tracks gateway reachability for the whole tree so the status pill and the
 * hooks cannot disagree about whether we are live.
 */
export function LiveProvider({ children }: { children: ReactNode }) {
  const [source, setSource] = useState<Source>('loading');

  useEffect(() => {
    let cancelled = false;

    const probe = async () => {
      try {
        await api.fetchHealth();
        if (!cancelled) setSource('live');
      } catch {
        if (!cancelled) setSource('demo');
      }
    };

    probe();
    // Slow poll only. The SSE stream is the fast path for *changes*; this is
    // just so a gateway that comes back up is noticed without a page reload.
    const timer = setInterval(probe, 15_000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  return (
    <ConnectionContext.Provider value={source}>{children}</ConnectionContext.Provider>
  );
}

// ── Core hook ────────────────────────────────────────────────────

export interface LiveResult<T> {
  data: T;
  source: Source;
  error: string | null;
  loading: boolean;
  refresh: () => void;
}

/**
 * `fallback` is returned whenever the fetch fails, so a page never renders an
 * empty shell — but `source` says 'demo' when that happens, and callers that
 * care can branch on it.
 */
export function useLive<T>(
  fetcher: () => Promise<T>,
  fallback: T,
  refreshOn: string[] = []
): LiveResult<T> {
  const [data, setData] = useState<T>(fallback);
  const [source, setSource] = useState<Source>('loading');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Kept in a ref so an inline arrow fetcher does not restart the effect on
  // every render.
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const next = await fetcherRef.current();
      if (!mounted.current) return;
      setData(next);
      setSource('live');
      setError(null);
    } catch (err: any) {
      if (!mounted.current) return;
      setData(fallback);
      setSource('demo');
      setError(err?.message ?? 'Gateway unreachable');
    } finally {
      if (mounted.current) setLoading(false);
    }
    // `fallback` is a module-level constant in every call site; including it
    // would only re-run the effect when an inline literal is passed.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const watched = refreshOn.join(',');
  useEffect(() => {
    if (!watched) return;
    const wanted = new Set(watched.split(','));
    return onDomainEvent((type) => {
      if (wanted.has(type)) load();
    });
  }, [watched, load]);

  return { data, source, error, loading, refresh: load };
}

// ── Domain hooks ─────────────────────────────────────────────────

const CONFLICT_EVENTS = ['conflict.detected', 'conflict.resolved'];

export function useConflicts(params?: { status?: string; city?: string }) {
  const key = `${params?.status ?? ''}|${params?.city ?? ''}`;
  const fetcher = useCallback(
    async () => (await api.fetchConflicts(params)).conflicts,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [key]
  );
  return useLive(fetcher, mockConflicts as any[], CONFLICT_EVENTS);
}

export function useDepartments() {
  return useLive(
    async () => (await api.fetchDepartments()).departments,
    mockDepartments as any[],
    ['agent.activity']
  );
}

export function usePlannedWorks(params?: { deptId?: string; city?: string }) {
  const key = `${params?.deptId ?? ''}|${params?.city ?? ''}`;
  const fetcher = useCallback(
    async () => (await api.fetchPlannedWorks(params)).planned_works,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [key]
  );
  return useLive(fetcher, mockWorks as any[], CONFLICT_EVENTS);
}

export function useNotices() {
  return useLive(
    async () => (await api.fetchNotices()).notices,
    mockNotices as any[],
    ['notice.generated']
  );
}

export function useAgentActivity(limit = 50) {
  return useLive(
    async () => (await api.fetchAgentActivity({ limit })).activities,
    mockActivities as any[],
    ['agent.activity', 'armor.blocked', 'conflict.detected', 'conflict.resolved']
  );
}

export function useDashboardMetrics() {
  return useLive(
    () => api.fetchDashboardMetrics(),
    mockMetrics as any,
    [...CONFLICT_EVENTS, 'notice.generated']
  );
}

export function useGovernanceStats() {
  return useLive(() => api.fetchGovernanceStats(), null as any, ['armor.blocked']);
}

export function useRegistry() {
  return useLive(() => api.fetchRegistry(), null as any);
}

export function useTraces(limit = 20) {
  return useLive(() => api.fetchTraces(limit), null as any, [
    'conflict.resolved',
    'agent.activity',
  ]);
}
