/**
 * DIYA API Client
 * Centralized API layer for all backend communication.
 * Currently uses mock data; swap USE_MOCK=false + set API_URL to connect to real backend.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const USE_MOCK = true; // Flip to false when backend is connected

// ── Generic fetch wrapper ───────────────────────────────────────

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// ── Department API ──────────────────────────────────────────────

export async function fetchDepartments() {
  return apiFetch<{ departments: any[]; count: number }>('/api/departments');
}

export async function fetchDepartment(deptId: string) {
  return apiFetch<any>(`/api/departments/${deptId}`);
}

// ── Planned Works API ───────────────────────────────────────────

export async function fetchPlannedWorks(params?: {
  deptId?: string;
  city?: string;
  status?: string;
}) {
  const query = new URLSearchParams();
  if (params?.deptId) query.set('dept_id', params.deptId);
  if (params?.city) query.set('city', params.city);
  if (params?.status) query.set('status', params.status);
  const qs = query.toString();
  return apiFetch<{ planned_works: any[]; count: number }>(
    `/api/planned-works${qs ? `?${qs}` : ''}`
  );
}

// ── Conflicts API ───────────────────────────────────────────────

export async function fetchConflicts(params?: { status?: string; city?: string }) {
  const query = new URLSearchParams();
  if (params?.status) query.set('status', params.status);
  if (params?.city) query.set('city', params.city);
  const qs = query.toString();
  return apiFetch<{ conflicts: any[]; count: number }>(
    `/api/conflicts${qs ? `?${qs}` : ''}`
  );
}

export async function fetchConflict(conflictId: string) {
  return apiFetch<any>(`/api/conflicts/${conflictId}`);
}

export async function resolveConflict(
  conflictId: string,
  data: { resolution_type?: string; notes?: string }
) {
  return apiFetch<any>(`/api/conflicts/${conflictId}/resolve`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ── Mesh API ────────────────────────────────────────────────────

export async function fetchMeshData(city: string) {
  return apiFetch<any>(`/api/mesh/${city}`);
}

// ── Notices API ─────────────────────────────────────────────────

export async function fetchNotices() {
  return apiFetch<{ notices: any[]; count: number }>('/api/notices');
}

// ── Agent API ───────────────────────────────────────────────────

export async function fetchAgentActivity(params?: { agentType?: string; limit?: number }) {
  const query = new URLSearchParams();
  if (params?.agentType) query.set('agent_type', params.agentType);
  if (params?.limit) query.set('limit', String(params.limit));
  const qs = query.toString();
  return apiFetch<{ activities: any[]; count: number }>(
    `/api/agents/activity${qs ? `?${qs}` : ''}`
  );
}

export async function fetchReasoningTrace(traceId: string) {
  return apiFetch<any>(`/api/agents/traces/${traceId}`);
}

// ── Dashboard API ───────────────────────────────────────────────

export async function fetchDashboardMetrics() {
  return apiFetch<any>('/api/dashboard/metrics');
}

// ── Citizen Complaint API (Model Armor demo) ────────────────────

export async function submitComplaint(data: {
  text: string;
  location?: string;
  contact?: string;
}) {
  return apiFetch<any>('/api/complaints', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ── SSE Event Stream ────────────────────────────────────────────

export function subscribeToEvents(
  onMessage: (event: any) => void,
  onError?: (error: any) => void
): () => void {
  const eventSource = new EventSource(`${API_URL}/api/events`);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch {
      onMessage(event.data);
    }
  };

  eventSource.onerror = (error) => {
    onError?.(error);
  };

  return () => eventSource.close();
}
