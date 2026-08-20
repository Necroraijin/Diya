import {
  Department,
  PlannedWork,
  Conflict,
  Notice,
  AgentActivity,
  ReasoningTrace,
  CityConfig,
  DashboardMetrics,
} from '@/types';

// ── Cities ──────────────────────────────────────────────────────────────────

export const cities: CityConfig[] = [
  {
    id: 'mumbai',
    name: 'Mumbai',
    center: [72.8777, 19.076],
    zoom: 14,
    bounds: [
      [72.82, 19.0],
      [72.94, 19.15],
    ],
    wards: ['A', 'B', 'C', 'D', 'E', 'F/N', 'F/S', 'G/N', 'G/S', 'H/E', 'H/W'],
  },
  {
    id: 'delhi',
    name: 'Delhi',
    center: [77.2295, 28.6139],
    zoom: 14,
    bounds: [
      [77.15, 28.55],
      [77.32, 28.7],
    ],
    wards: ['Civil Lines', 'Karol Bagh', 'Connaught Place', 'Chandni Chowk', 'Sadar Bazaar'],
  },
];

// ── Departments ─────────────────────────────────────────────────────────────

export const departments: Department[] = [
  {
    id: 'dept-roads',
    name: 'Roads & Bridges Department',
    shortName: 'Roads',
    agentIdentityId: 'agent-identity-roads-001',
    color: '#ffffff',
    icon: 'road',
    activeWorks: 12,
    agentStatus: 'online',
  },
  {
    id: 'dept-water',
    name: 'Water Supply & Sewerage Department',
    shortName: 'Water',
    agentIdentityId: 'agent-identity-water-001',
    color: '#a0a0a0',
    icon: 'droplets',
    activeWorks: 8,
    agentStatus: 'online',
  },
  {
    id: 'dept-telecom',
    name: 'Telecom & Fiber Infrastructure',
    shortName: 'Telecom',
    agentIdentityId: 'agent-identity-telecom-001',
    color: '#666666',
    icon: 'wifi',
    activeWorks: 15,
    agentStatus: 'processing',
  },
  {
    id: 'dept-sewage',
    name: 'Sewage & Drainage Department',
    shortName: 'Sewage',
    agentIdentityId: 'agent-identity-sewage-001',
    color: '#444444',
    icon: 'waves',
    activeWorks: 6,
    agentStatus: 'online',
  },
];

// ── Planned Works (Mumbai) ──────────────────────────────────────────────────

export const plannedWorks: PlannedWork[] = [
  // Mumbai - Roads
  {
    id: 'pw-mum-001',
    deptId: 'dept-roads',
    deptName: 'Roads',
    title: 'SV Road Resurfacing - Andheri West',
    description: 'Complete bituminous resurfacing of SV Road from Andheri station junction to Juhu Circle. Includes pothole repair, drainage cover replacement, and road marking.',
    location: { lat: 19.1197, lng: 72.8464, wayId: 'way-48213001', streetName: 'SV Road', ward: 'K/W' },
    geofenceRadius: 200,
    startDate: '2026-09-15',
    endDate: '2026-10-30',
    workType: 'Resurfacing',
    status: 'conflicted',
    budget: 45000000,
    city: 'mumbai',
  },
  {
    id: 'pw-mum-002',
    deptId: 'dept-roads',
    deptName: 'Roads',
    title: 'LBS Marg Flyover Repair - Kurla',
    description: 'Structural repair and waterproofing of LBS Marg flyover near Kurla terminus. Expansion joint replacement and bearing pad renewal.',
    location: { lat: 19.0726, lng: 72.8793, wayId: 'way-48213002', streetName: 'LBS Marg', ward: 'L' },
    geofenceRadius: 150,
    startDate: '2026-10-01',
    endDate: '2026-11-15',
    workType: 'Structural Repair',
    status: 'planned',
    budget: 78000000,
    city: 'mumbai',
  },
  {
    id: 'pw-mum-003',
    deptId: 'dept-roads',
    deptName: 'Roads',
    title: 'FC Road Widening - Dadar',
    description: 'Road widening along FC Road near Shivaji Park with new pedestrian pathway and cycle track.',
    location: { lat: 19.0186, lng: 72.8429, wayId: 'way-48213003', streetName: 'FC Road', ward: 'G/N' },
    geofenceRadius: 180,
    startDate: '2026-09-01',
    endDate: '2026-12-15',
    workType: 'Widening',
    status: 'planned',
    budget: 120000000,
    city: 'mumbai',
  },
  // Mumbai - Water
  {
    id: 'pw-mum-004',
    deptId: 'dept-water',
    deptName: 'Water',
    title: 'Water Main Replacement - SV Road Segment',
    description: 'Replacement of 900mm CI water main along SV Road from DN Nagar to Irla Bridge. Includes valve chamber construction and new service connections.',
    location: { lat: 19.1185, lng: 72.8451, wayId: 'way-48213001', streetName: 'SV Road', ward: 'K/W' },
    geofenceRadius: 200,
    startDate: '2026-10-01',
    endDate: '2026-11-30',
    workType: 'Water Main Replacement',
    status: 'conflicted',
    budget: 35000000,
    city: 'mumbai',
  },
  {
    id: 'pw-mum-005',
    deptId: 'dept-water',
    deptName: 'Water',
    title: 'Bandra Pipeline Extension',
    description: 'Extension of 600mm water pipeline from Bandra Reclamation to Carter Road with new distribution network.',
    location: { lat: 19.0544, lng: 72.8264, wayId: 'way-48213005', streetName: 'Carter Road', ward: 'H/W' },
    geofenceRadius: 250,
    startDate: '2026-11-01',
    endDate: '2027-01-15',
    workType: 'Pipeline Extension',
    status: 'planned',
    budget: 55000000,
    city: 'mumbai',
  },
  // Mumbai - Telecom
  {
    id: 'pw-mum-006',
    deptId: 'dept-telecom',
    deptName: 'Telecom',
    title: 'OFC Laying - SV Road to Link Road',
    description: 'Optical fiber cable laying from SV Road junction through internal roads to Link Road. HDPE duct installation with 96-fiber cable.',
    location: { lat: 19.1201, lng: 72.8470, wayId: 'way-48213001', streetName: 'SV Road', ward: 'K/W' },
    geofenceRadius: 150,
    startDate: '2026-09-20',
    endDate: '2026-10-20',
    workType: 'OFC Laying',
    status: 'conflicted',
    budget: 12000000,
    city: 'mumbai',
  },
  {
    id: 'pw-mum-007',
    deptId: 'dept-telecom',
    deptName: 'Telecom',
    title: '5G Small Cell Installation - BKC',
    description: 'Installation of 25 5G small cells along BKC connector roads with fiber backhaul.',
    location: { lat: 19.0660, lng: 72.8693, wayId: 'way-48213007', streetName: 'BKC Road', ward: 'H/E' },
    geofenceRadius: 500,
    startDate: '2026-10-15',
    endDate: '2026-12-30',
    workType: '5G Installation',
    status: 'planned',
    budget: 28000000,
    city: 'mumbai',
  },
  // Mumbai - Sewage
  {
    id: 'pw-mum-008',
    deptId: 'dept-sewage',
    deptName: 'Sewage',
    title: 'Storm Drain Upgrade - Andheri Subway',
    description: 'Upgrade of storm water drain capacity near Andheri subway. Box drain construction with increased cross-section to prevent waterlogging.',
    location: { lat: 19.1190, lng: 72.8458, wayId: 'way-48213001', streetName: 'SV Road', ward: 'K/W' },
    geofenceRadius: 180,
    startDate: '2026-10-15',
    endDate: '2026-12-15',
    workType: 'Storm Drain Upgrade',
    status: 'conflicted',
    budget: 42000000,
    city: 'mumbai',
  },
  // Delhi - Roads
  {
    id: 'pw-del-001',
    deptId: 'dept-roads',
    deptName: 'Roads',
    title: 'Chandni Chowk Road Restoration',
    description: 'Post-monsoon restoration of Chandni Chowk main road. Milling and re-laying of bituminous surface with improved camber.',
    location: { lat: 28.6562, lng: 77.2310, wayId: 'way-92001001', streetName: 'Chandni Chowk Road', ward: 'Chandni Chowk' },
    geofenceRadius: 200,
    startDate: '2026-09-10',
    endDate: '2026-10-25',
    workType: 'Restoration',
    status: 'conflicted',
    budget: 38000000,
    city: 'delhi',
  },
  // Delhi - Water
  {
    id: 'pw-del-002',
    deptId: 'dept-water',
    deptName: 'Water',
    title: 'DJB Pipeline Relaying - Chandni Chowk',
    description: 'Relaying of aged 450mm DI pipeline under Chandni Chowk Road. Includes house service connection renewals.',
    location: { lat: 28.6558, lng: 77.2305, wayId: 'way-92001001', streetName: 'Chandni Chowk Road', ward: 'Chandni Chowk' },
    geofenceRadius: 200,
    startDate: '2026-09-25',
    endDate: '2026-11-10',
    workType: 'Pipeline Relaying',
    status: 'conflicted',
    budget: 25000000,
    city: 'delhi',
  },
  // Delhi - Telecom
  {
    id: 'pw-del-003',
    deptId: 'dept-telecom',
    deptName: 'Telecom',
    title: 'FTTH Network Expansion - Karol Bagh',
    description: 'Fiber-to-the-home network expansion covering 15 blocks in Karol Bagh area.',
    location: { lat: 28.6519, lng: 77.1909, wayId: 'way-92001003', streetName: 'Ajmal Khan Road', ward: 'Karol Bagh' },
    geofenceRadius: 400,
    startDate: '2026-10-01',
    endDate: '2026-12-15',
    workType: 'FTTH Expansion',
    status: 'planned',
    budget: 18000000,
    city: 'delhi',
  },
  {
    id: 'pw-del-004',
    deptId: 'dept-telecom',
    deptName: 'Telecom',
    title: 'Duct Repair - Connaught Place Inner Circle',
    description: 'Repair and cleaning of existing telecom ducts along CP inner circle. Cable pulling for upgraded capacity.',
    location: { lat: 28.6315, lng: 77.2167, wayId: 'way-92001004', streetName: 'Connaught Place', ward: 'Connaught Place' },
    geofenceRadius: 300,
    startDate: '2026-09-05',
    endDate: '2026-09-30',
    workType: 'Duct Repair',
    status: 'completed',
    budget: 8000000,
    city: 'delhi',
  },
  // Delhi - Sewage
  {
    id: 'pw-del-005',
    deptId: 'dept-sewage',
    deptName: 'Sewage',
    title: 'Sewer Line Rehabilitation - Chandni Chowk',
    description: 'Trenchless rehabilitation of 600mm sewer line using CIPP method under Chandni Chowk Road.',
    location: { lat: 28.6565, lng: 77.2315, wayId: 'way-92001001', streetName: 'Chandni Chowk Road', ward: 'Chandni Chowk' },
    geofenceRadius: 180,
    startDate: '2026-10-10',
    endDate: '2026-11-20',
    workType: 'Sewer Rehabilitation',
    status: 'conflicted',
    budget: 15000000,
    city: 'delhi',
  },
];

// ── Conflicts ───────────────────────────────────────────────────────────────

export const conflicts: Conflict[] = [
  {
    id: 'conf-001',
    workIds: ['pw-mum-001', 'pw-mum-004', 'pw-mum-006', 'pw-mum-008'],
    works: plannedWorks.filter((w) =>
      ['pw-mum-001', 'pw-mum-004', 'pw-mum-006', 'pw-mum-008'].includes(w.id)
    ),
    overlapType: 'both',
    proposedWindow: { start: '2026-09-15', end: '2026-12-15' },
    status: 'detected',
    reasoningTrace:
      'Detected 4-way conflict on SV Road, Andheri West (Ward K/W). All four departments have planned works within a 200m radius on the same road segment (wayId: way-48213001). Temporal overlap spans Sep 15 - Dec 15, 2026. Proposed consolidated window: complete all underground work (water main, OFC, storm drain) first (Sep 15 - Nov 15), then surface work (resurfacing) last (Nov 15 - Dec 15). Estimated savings: 3.2 Cr from shared traffic management, single mobilization, and reduced repeated restoration costs.',
    detectedAt: '2026-08-20T10:30:00Z',
    severity: 'critical',
    savings: 32000000,
    city: 'mumbai',
  },
  {
    id: 'conf-002',
    workIds: ['pw-del-001', 'pw-del-002', 'pw-del-005'],
    works: plannedWorks.filter((w) =>
      ['pw-del-001', 'pw-del-002', 'pw-del-005'].includes(w.id)
    ),
    overlapType: 'both',
    proposedWindow: { start: '2026-09-10', end: '2026-11-20' },
    status: 'detected',
    reasoningTrace:
      'Detected 3-way conflict on Chandni Chowk Road, Delhi (Ward: Chandni Chowk). Roads Dept restoration, DJB pipeline relaying, and sewer rehabilitation all target the same road segment within 200m. Temporal overlap: Sep 10 - Nov 20, 2026. Proposed sequence: sewer rehabilitation (trenchless, minimal surface disruption) → pipeline relaying → road restoration as final step. Estimated savings: 1.8 Cr.',
    detectedAt: '2026-08-20T11:15:00Z',
    severity: 'critical',
    savings: 18000000,
    city: 'delhi',
  },
  {
    id: 'conf-003',
    workIds: ['pw-mum-002', 'pw-mum-007'],
    works: plannedWorks.filter((w) =>
      ['pw-mum-002', 'pw-mum-007'].includes(w.id)
    ),
    overlapType: 'temporal',
    proposedWindow: { start: '2026-10-01', end: '2026-12-30' },
    status: 'resolved',
    reasoningTrace:
      'Temporal overlap detected between LBS Marg flyover repair and BKC 5G installation. Spatial overlap minimal (different road segments, 2.1km apart). However, both require traffic diversions on the same arterial route. Proposed: stagger traffic management plans with shared diversion routes. Resolved with minor schedule adjustment.',
    detectedAt: '2026-08-19T14:00:00Z',
    resolvedAt: '2026-08-20T09:00:00Z',
    severity: 'medium',
    savings: 5000000,
    city: 'mumbai',
  },
  {
    id: 'conf-004',
    workIds: ['pw-mum-003', 'pw-mum-005'],
    works: plannedWorks.filter((w) =>
      ['pw-mum-003', 'pw-mum-005'].includes(w.id)
    ),
    overlapType: 'spatial',
    proposedWindow: { start: '2026-09-01', end: '2027-01-15' },
    status: 'dismissed',
    reasoningTrace:
      'Spatial proximity flagged between FC Road widening (Dadar) and Bandra pipeline extension. After review: different wards (G/N vs H/W), separate road segments, no shared traffic impact zone. False positive — geofence radii overlapped at boundary but works are operationally independent. Dismissed.',
    detectedAt: '2026-08-18T16:30:00Z',
    severity: 'low',
    savings: 0,
    city: 'mumbai',
  },
];

// ── Notices ──────────────────────────────────────────────────────────────────

export const notices: Notice[] = [
  {
    id: 'notice-001',
    conflictId: 'conf-003',
    title: 'Consolidated Road Works Notice - LBS Marg & BKC Area',
    description:
      'The Municipal Corporation informs citizens that coordinated infrastructure works will be undertaken on LBS Marg (Kurla) and BKC connector roads from October 1 to December 30, 2026. Traffic diversions will be coordinated to minimize disruption. A shared traffic management plan has been approved.',
    affectedArea: 'LBS Marg (Kurla Terminus to Sion Junction) & BKC Connector Roads',
    closureWindow: { start: '2026-10-01', end: '2026-12-30' },
    departments: ['Roads & Bridges', 'Telecom & Fiber'],
    pdfUrl: '/notices/notice-001.pdf',
    icsUrl: '/notices/notice-001.ics',
    generatedAt: '2026-08-20T09:15:00Z',
    status: 'published',
  },
];

// ── Agent Activity ──────────────────────────────────────────────────────────

export const agentActivities: AgentActivity[] = [
  {
    id: 'act-001',
    agentName: 'Roads Department Agent',
    agentType: 'department',
    action: 'Feed Ingestion',
    detail: 'Normalized 3 planned works records from Roads & Bridges Department feed for Mumbai.',
    timestamp: '2026-08-20T10:00:00Z',
    status: 'success',
    duration: 2340,
  },
  {
    id: 'act-002',
    agentName: 'Water Department Agent',
    agentType: 'department',
    action: 'Feed Ingestion',
    detail: 'Normalized 2 planned works records from Water Supply Department feed for Mumbai.',
    timestamp: '2026-08-20T10:05:00Z',
    status: 'success',
    duration: 1890,
  },
  {
    id: 'act-003',
    agentName: 'Telecom Department Agent',
    agentType: 'department',
    action: 'Feed Ingestion',
    detail: 'Normalized 2 planned works records from Telecom Department feed. 1 record flagged for incomplete geolocation.',
    timestamp: '2026-08-20T10:08:00Z',
    status: 'success',
    duration: 3100,
  },
  {
    id: 'act-004',
    agentName: 'Coordinator Agent',
    agentType: 'coordinator',
    action: 'Conflict Detection',
    detail: 'Detected 4-way spatial+temporal conflict on SV Road, Andheri West. 4 departments, same road segment. Severity: CRITICAL.',
    timestamp: '2026-08-20T10:30:00Z',
    status: 'success',
    traceId: 'trace-001',
    duration: 8750,
  },
  {
    id: 'act-005',
    agentName: 'Coordinator Agent',
    agentType: 'coordinator',
    action: 'Cross-Department Read',
    detail: 'BLOCKED: Roads Agent attempted to read Water Department collection. Agent Identity scope violation. Access denied.',
    timestamp: '2026-08-20T10:12:00Z',
    status: 'blocked',
    duration: 45,
  },
  {
    id: 'act-006',
    agentName: 'Coordinator Agent',
    agentType: 'coordinator',
    action: 'Conflict Resolution',
    detail: 'Resolved temporal conflict between LBS Marg flyover repair and BKC 5G installation. Proposed staggered traffic management.',
    timestamp: '2026-08-20T09:00:00Z',
    status: 'success',
    traceId: 'trace-002',
    duration: 12400,
  },
  {
    id: 'act-007',
    agentName: 'Citizen Notice Agent',
    agentType: 'notice',
    action: 'Notice Generation',
    detail: 'Generated public works notice PDF and ICS file for resolved conflict conf-003 (LBS Marg & BKC area).',
    timestamp: '2026-08-20T09:15:00Z',
    status: 'success',
    duration: 4200,
  },
  {
    id: 'act-008',
    agentName: 'Coordinator Agent',
    agentType: 'coordinator',
    action: 'Model Armor Check',
    detail: 'BLOCKED: Citizen complaint text contained prompt injection attempt. Input sanitized by Model Armor before reaching agent.',
    timestamp: '2026-08-20T08:45:00Z',
    status: 'blocked',
    duration: 120,
  },
  {
    id: 'act-009',
    agentName: 'Sewage Department Agent',
    agentType: 'department',
    action: 'Feed Ingestion',
    detail: 'Normalized 1 planned work record from Sewage & Drainage Department feed for Mumbai.',
    timestamp: '2026-08-20T10:10:00Z',
    status: 'success',
    duration: 1560,
  },
  {
    id: 'act-010',
    agentName: 'Coordinator Agent',
    agentType: 'coordinator',
    action: 'Memory Bank Update',
    detail: 'Stored resolution for conf-003 in Memory Bank. Cross-session state updated. 2 active conflicts remain in working memory.',
    timestamp: '2026-08-20T09:02:00Z',
    status: 'success',
    duration: 890,
  },
];

// ── Reasoning Traces ────────────────────────────────────────────────────────

export const reasoningTraces: ReasoningTrace[] = [
  {
    id: 'trace-001',
    agentName: 'Coordinator Agent',
    conflictId: 'conf-001',
    steps: [
      {
        step: 1,
        action: 'Spatial Scan',
        reasoning: 'Scanning all planned_works records for spatial overlap using geofence intersection. Threshold: 50m overlap.',
        result: 'Found 4 records within 200m radius on wayId: way-48213001 (SV Road, Andheri West)',
        timestamp: '2026-08-20T10:30:01Z',
        duration: 1200,
      },
      {
        step: 2,
        action: 'Temporal Analysis',
        reasoning: 'Checking date window overlaps for the 4 spatially co-located works. Any overlap > 7 days is flagged.',
        result: 'All 4 works overlap between Oct 1 - Oct 20, 2026 (20-day window). Full span: Sep 15 - Dec 15.',
        timestamp: '2026-08-20T10:30:03Z',
        duration: 800,
      },
      {
        step: 3,
        action: 'Dependency Graph',
        reasoning: 'Building work-type dependency graph. Underground utilities must complete before surface work. Sequence: Sewage → Water → Telecom (duct) → Roads (surface).',
        result: 'Optimal sequence determined: storm drain → water main → OFC duct → resurfacing',
        timestamp: '2026-08-20T10:30:05Z',
        duration: 2100,
      },
      {
        step: 4,
        action: 'Window Calculation',
        reasoning: 'Calculating consolidated window with buffer days between phases. Each department gets a dedicated sub-window.',
        result: 'Proposed: Storm drain (Sep 15 - Oct 15) → Water main (Oct 10 - Nov 10) → OFC (Oct 25 - Nov 15) → Resurfacing (Nov 15 - Dec 15). Some parallel work possible for non-conflicting segments.',
        timestamp: '2026-08-20T10:30:07Z',
        duration: 1500,
      },
      {
        step: 5,
        action: 'Savings Estimation',
        reasoning: 'Estimating cost savings from consolidated execution: shared traffic management (~80L), single mobilization/demobilization (~1.2Cr), reduced repeated restoration (~1.2Cr), citizen disruption reduction (qualitative).',
        result: 'Estimated total savings: Rs 3.2 Crore. Citizen disruption reduced from 4 separate closures to 1 consolidated closure.',
        timestamp: '2026-08-20T10:30:08Z',
        duration: 1150,
      },
    ],
    totalDuration: 8750,
    outcome: 'CRITICAL conflict detected. 4-department consolidated window proposed. Awaiting department acknowledgment.',
  },
];

// ── Dashboard Metrics ───────────────────────────────────────────────────────

export const dashboardMetrics: DashboardMetrics = {
  totalConflicts: 4,
  resolvedConflicts: 1,
  activeWorks: 15,
  departments: 4,
  estimatedSavings: 55000000,
  citizenNotices: 1,
  conflictTrend: [
    { date: '2026-08-14', detected: 0, resolved: 0 },
    { date: '2026-08-15', detected: 1, resolved: 0 },
    { date: '2026-08-16', detected: 1, resolved: 0 },
    { date: '2026-08-17', detected: 2, resolved: 0 },
    { date: '2026-08-18', detected: 3, resolved: 0 },
    { date: '2026-08-19', detected: 3, resolved: 1 },
    { date: '2026-08-20', detected: 4, resolved: 1 },
  ],
  departmentBreakdown: [
    { name: 'Roads', works: 5, conflicts: 3 },
    { name: 'Water', works: 4, conflicts: 2 },
    { name: 'Telecom', works: 4, conflicts: 2 },
    { name: 'Sewage', works: 2, conflicts: 2 },
  ],
};

// ── Map Mock Data (Building Polygons for mesh rendering) ────────────────────

export const mumbaiBuildings = [
  { coordinates: [[72.8450, 19.1190], [72.8460, 19.1190], [72.8460, 19.1200], [72.8450, 19.1200]], height: 30, wayId: 'bld-001' },
  { coordinates: [[72.8462, 19.1188], [72.8472, 19.1188], [72.8472, 19.1198], [72.8462, 19.1198]], height: 45, wayId: 'bld-002' },
  { coordinates: [[72.8440, 19.1195], [72.8448, 19.1195], [72.8448, 19.1205], [72.8440, 19.1205]], height: 20, wayId: 'bld-003' },
  { coordinates: [[72.8474, 19.1192], [72.8484, 19.1192], [72.8484, 19.1202], [72.8474, 19.1202]], height: 55, wayId: 'bld-004' },
  { coordinates: [[72.8445, 19.1178], [72.8455, 19.1178], [72.8455, 19.1188], [72.8445, 19.1188]], height: 35, wayId: 'bld-005' },
  { coordinates: [[72.8465, 19.1175], [72.8478, 19.1175], [72.8478, 19.1185], [72.8465, 19.1185]], height: 60, wayId: 'bld-006' },
  { coordinates: [[72.8435, 19.1205], [72.8445, 19.1205], [72.8445, 19.1215], [72.8435, 19.1215]], height: 25, wayId: 'bld-007' },
  { coordinates: [[72.8455, 19.1208], [72.8468, 19.1208], [72.8468, 19.1218], [72.8455, 19.1218]], height: 40, wayId: 'bld-008' },
  { coordinates: [[72.8480, 19.1205], [72.8490, 19.1205], [72.8490, 19.1212], [72.8480, 19.1212]], height: 50, wayId: 'bld-009' },
  { coordinates: [[72.8430, 19.1170], [72.8442, 19.1170], [72.8442, 19.1180], [72.8430, 19.1180]], height: 28, wayId: 'bld-010' },
];

export const mumbaiRoads = [
  { path: [[72.8430, 19.1197], [72.8440, 19.1197], [72.8450, 19.1197], [72.8460, 19.1197], [72.8470, 19.1197], [72.8480, 19.1197], [72.8490, 19.1197]], wayId: 'way-48213001', name: 'SV Road', width: 4 },
  { path: [[72.8450, 19.1170], [72.8450, 19.1180], [72.8450, 19.1190], [72.8450, 19.1200], [72.8450, 19.1210], [72.8450, 19.1220]], wayId: 'way-48213010', name: 'DN Nagar Road', width: 3 },
  { path: [[72.8470, 19.1170], [72.8470, 19.1180], [72.8470, 19.1190], [72.8470, 19.1200], [72.8470, 19.1210]], wayId: 'way-48213011', name: 'Link Road', width: 3 },
  { path: [[72.8435, 19.1185], [72.8445, 19.1185], [72.8455, 19.1185], [72.8465, 19.1185], [72.8475, 19.1185], [72.8485, 19.1185]], wayId: 'way-48213012', name: 'Juhu Lane', width: 2 },
  { path: [[72.8435, 19.1210], [72.8445, 19.1210], [72.8455, 19.1210], [72.8465, 19.1210], [72.8475, 19.1210], [72.8485, 19.1210]], wayId: 'way-48213013', name: 'Irla Road', width: 2 },
];

export const conflictZones = [
  { center: [72.8464, 19.1197] as [number, number], radius: 200, conflictId: 'conf-001', severity: 'critical' as const },
];

export const delhiBuildings = [
  { coordinates: [[77.2300, 28.6555], [77.2310, 28.6555], [77.2310, 28.6565], [77.2300, 28.6565]], height: 15, wayId: 'bld-d001' },
  { coordinates: [[77.2312, 28.6558], [77.2322, 28.6558], [77.2322, 28.6568], [77.2312, 28.6568]], height: 12, wayId: 'bld-d002' },
  { coordinates: [[77.2290, 28.6560], [77.2298, 28.6560], [77.2298, 28.6570], [77.2290, 28.6570]], height: 18, wayId: 'bld-d003' },
  { coordinates: [[77.2305, 28.6570], [77.2315, 28.6570], [77.2315, 28.6580], [77.2305, 28.6580]], height: 10, wayId: 'bld-d004' },
  { coordinates: [[77.2318, 28.6548], [77.2328, 28.6548], [77.2328, 28.6558], [77.2318, 28.6558]], height: 14, wayId: 'bld-d005' },
];

export const delhiRoads = [
  { path: [[77.2280, 28.6562], [77.2290, 28.6562], [77.2300, 28.6562], [77.2310, 28.6562], [77.2320, 28.6562], [77.2330, 28.6562]], wayId: 'way-92001001', name: 'Chandni Chowk Road', width: 4 },
  { path: [[77.2305, 28.6545], [77.2305, 28.6555], [77.2305, 28.6565], [77.2305, 28.6575], [77.2305, 28.6585]], wayId: 'way-92001010', name: 'Nai Sarak', width: 2 },
];
