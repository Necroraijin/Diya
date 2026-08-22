/**
 * DIYA API Client
 * Centralized API layer for all backend communication.
 *
 * Every function here hits the live gateway. `USE_MOCK` used to sit at the top
 * of this file but was never read by anything — pages import from mock-data.ts
 * directly. Wiring the pages to these functions is Phase 5.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

/** Re-run deterministic detection over every planned work. */
export async function detectConflicts(city?: string) {
  return apiFetch<any>(`/api/conflicts/detect${city ? `?city=${city}` : ''}`, {
    method: 'POST',
  });
}

// ── Mesh API ────────────────────────────────────────────────────

export async function fetchMeshData(city: string) {
  return apiFetch<any>(`/api/mesh/${city}`);
}

/** Dissolved GeoJSON polygons for the overlapping geofences in a city. */
export async function fetchConflictZones(city: string) {
  return apiFetch<any>(`/api/mesh/${city}/conflict-zones`);
}

export async function fetchCities() {
  return apiFetch<{ cities: any[] }>('/api/cities');
}

// ── Notices API ─────────────────────────────────────────────────

export async function fetchNotices() {
  return apiFetch<{ notices: any[]; count: number }>('/api/notices');
}

export async function fetchNotice(noticeId: string) {
  return apiFetch<any>(`/api/notices/${noticeId}`);
}

/**
 * Direct link to a generated artifact. The gateway streams these back from the
 * notice service, so they are plain hrefs rather than fetch calls.
 */
export function noticeArtifactUrl(noticeId: string, artifact: 'pdf' | 'ics') {
  return `${API_URL}/api/notices/${noticeId}/${artifact}`;
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

// ── Governance API ──────────────────────────────────────────────

export async function verifyIdentity(params: {
  agentId: string;
  resource: string;
  action?: string;
}) {
  const query = new URLSearchParams({
    agent_id: params.agentId,
    resource: params.resource,
    action: params.action ?? 'read',
  });
  return apiFetch<any>(`/api/governance/identity/verify?${query}`);
}

/** Screen text without submitting it as a complaint. */
export async function scanWithArmor(text: string) {
  return apiFetch<any>('/api/governance/armor/scan', {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
}

export async function fetchGovernanceStats() {
  return apiFetch<any>('/api/governance/stats');
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
