export interface Department {
  id: string;
  name: string;
  shortName: string;
  agentIdentityId: string;
  color: string;
  icon: string;
  activeWorks: number;
  agentStatus: 'online' | 'offline' | 'processing';
}

export interface PlannedWork {
  id: string;
  deptId: string;
  deptName: string;
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
  works: PlannedWork[];
  overlapType: 'spatial' | 'temporal' | 'both';
  proposedWindow: {
    start: string;
    end: string;
  };
  status: 'detected' | 'resolved' | 'dismissed';
  reasoningTrace: string;
  detectedAt: string;
  resolvedAt?: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  savings: number;
  city: string;
}

export interface MeshEdit {
  id: string;
  targetWayId: string;
  editType: 'highlight' | 'reroute' | 'flag';
  color: string;
  conflictId: string;
  issuedByAgent: string;
  timestamp: string;
}

export interface Notice {
  id: string;
  conflictId: string;
  title: string;
  description: string;
  affectedArea: string;
  closureWindow: {
    start: string;
    end: string;
  };
  departments: string[];
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

export interface ReasoningTrace {
  id: string;
  agentName: string;
  conflictId: string;
  steps: {
    step: number;
    action: string;
    reasoning: string;
    result: string;
    timestamp: string;
    duration: number;
  }[];
  totalDuration: number;
  outcome: string;
}

export interface CityConfig {
  id: string;
  name: string;
  center: [number, number];
  zoom: number;
  bounds: [[number, number], [number, number]];
  wards: string[];
}

export interface MapLayer {
  id: string;
  name: string;
  visible: boolean;
  type: 'buildings' | 'roads' | 'conflicts' | 'works' | 'zones';
}

export interface DashboardMetrics {
  totalConflicts: number;
  resolvedConflicts: number;
  activeWorks: number;
  departments: number;
  estimatedSavings: number;
  citizenNotices: number;
  conflictTrend: { date: string; detected: number; resolved: number }[];
  departmentBreakdown: { name: string; works: number; conflicts: number }[];
}
