// Shared type definitions between frontend and backend services

export interface Department {
  id: string;
  name: string;
  shortName: string;
  agentIdentityId: string;
  agentStatus: 'online' | 'offline' | 'processing';
}

export interface PlannedWork {
  id: string;
  deptId: string;
  title: string;
  description: string;
  location: {
    lat: number;
    lng: number;
    wayId: string;
    streetName: string;
    ward: string;
  };
  geofenceRadius: number;
  startDate: string;
  endDate: string;
  workType: string;
  status: 'planned' | 'in-progress' | 'completed' | 'conflicted';
  budget: number;
  city: string;
}

export interface Conflict {
  id: string;
  workIds: string[];
  overlapType: 'spatial' | 'temporal' | 'both';
  proposedWindow: { start: string; end: string };
  status: 'detected' | 'resolved' | 'dismissed';
  reasoningTrace: string;
  detectedAt: string;
  resolvedAt?: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  savings: number;
  city: string;
}

export interface Notice {
  id: string;
  conflictId: string;
  title: string;
  pdfUrl: string;
  icsUrl: string;
  generatedAt: string;
  status: 'draft' | 'published' | 'expired';
}

export interface AgentActivity {
  id: string;
  agentName: string;
  agentType: 'department' | 'coordinator' | 'notice';
  action: string;
  detail: string;
  timestamp: string;
  status: 'success' | 'error' | 'processing' | 'blocked';
  traceId?: string;
  duration?: number;
}
