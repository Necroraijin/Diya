# DIYA - Build Plan

## Project Overview
DIYA (Dig Infrastructure Yielding Alignment) is a multi-agent infrastructure conflict resolution system that prevents municipal departments from repeatedly digging up the same roads. It uses AI agents to detect spatial/temporal conflicts across department plans and resolves them into consolidated work windows.

## Architecture: Microservices

```
diya/
├── apps/
│   ├── web/              → Next.js 14 frontend (TypeScript, Tailwind, deck.gl)
│   ├── api-gateway/      → FastAPI central API gateway (Python)
│   ├── agent-service/    → ADK agent orchestration service (Python)
│   ├── mesh-service/     → GIS/OSM data processing service (Python)
│   └── notice-service/   → PDF/ICS citizen notice generation (Python)
├── packages/
│   └── shared/           → Shared TypeScript types and schemas
├── data/
│   └── synthetic/        → Realistic seed data for Mumbai, Delhi
├── docker/               → Docker Compose + per-service Dockerfiles
├── infra/                → GCP Terraform configs
├── scripts/              → Utility scripts (setup, seed, dev)
└── docs/                 → plan.md, implementation.md
```

## Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS | Modern React framework with SSR/SSG, type safety |
| 3D Visualization | deck.gl + maplibre-gl | Best-in-class geospatial rendering, extruded polygons, wireframe support |
| Animations | Framer Motion | Production-grade animation library for subtle UI transitions |
| Charts | Recharts | Lightweight, composable charting for dashboard metrics |
| Icons | Lucide React | Clean, consistent icon set |
| API Gateway | FastAPI (Python) | High-performance async API, auto-docs, Pydantic validation |
| Agent Service | Google ADK (Python) | Mandatory hackathon requirement, native Gemini integration |
| Mesh Service | FastAPI + OSMnx/Shapely | GIS processing, spatial overlap detection |
| Notice Service | FastAPI + ReportLab/icalendar | PDF/ICS artifact generation |
| Database | Firestore | Native GCP, real-time listeners, document model fits the data |
| Message Queue | Pub/Sub | Async department feed ingestion |
| Storage | Cloud Storage | PDF/ICS artifact hosting |
| Containerization | Docker + Docker Compose | Local dev parity, GCP Cloud Run deployment |
| Infrastructure | Terraform | Reproducible GCP resource provisioning |

## Build Phases

### Phase 1: Foundation (Day 1-2) -- CURRENT
- [x] Project structure and monorepo setup
- [x] plan.md and implementation.md
- [x] Next.js frontend scaffolding with Tailwind
- [x] Design system: monochromatic black/white theme
- [x] Core UI components (Button, Card, Badge, etc.)
- [x] Layout shell (Sidebar, TopBar, AppShell)
- [x] Dashboard page with metric cards and charts
- [x] 3D map page with deck.gl wireframe mesh
- [x] Conflicts management page
- [x] Departments page
- [x] Citizen notices page
- [x] Agent activity/observability page
- [x] Mock data layer for all pages
- [x] Docker configuration for all services
- [x] Synthetic data generation (Mumbai + Delhi)

### Phase 2: Backend Services (Day 3-4)
- [ ] FastAPI gateway with all endpoints
- [ ] Firestore schema and connection
- [ ] Pub/Sub topic setup and ingestion pipeline
- [ ] Mesh service: OSM data fetch, spatial processing
- [ ] Notice service: PDF/ICS generation
- [ ] SSE/WebSocket real-time updates

### Phase 3: Agent Layer (Day 5-7)
- [ ] ADK agent scaffolding
- [ ] Department Agents (normalize feeds)
- [ ] Coordinator Agent (conflict detection)
- [ ] Citizen Notice Agent (artifact generation)
- [ ] Agent orchestration (ParallelAgent + SequentialAgent)
- [ ] Memory Bank integration for cross-session state

### Phase 4: Governance & Security (Day 8-9)
- [ ] Agent Identity scoping per department
- [ ] Agent Gateway configuration
- [ ] Model Armor on citizen input surface
- [ ] Agent Observability / Cloud Trace
- [ ] Agent Registry configuration
- [ ] Cross-department read denial demo

### Phase 5: Integration & Polish (Day 10-11)
- [ ] End-to-end integration testing
- [ ] Frontend connected to live backend
- [ ] SSE live mesh updates
- [ ] Failure mode testing (agent loops, malformed data)
- [ ] Architecture diagram (clean visual)
- [ ] README with setup instructions

### Phase 6: Submission (Day 12)
- [ ] Demo video recording (~4 min)
- [ ] Text description
- [ ] Final repo cleanup and license
- [ ] Submit before IST-adjusted deadline (Sep 1, 5:30am IST)

## Design Philosophy

### Visual Design: "Palantir-grade"
- Monochromatic black (#000000 - #0a0a0a) background
- White (#ffffff) and gray (#888888) text hierarchy
- Minimal accent colors only for status (conflict/resolved/pending)
- Thin borders (#1a1a1a - #222222)
- Subtle glassmorphism on cards
- Smooth Framer Motion transitions
- Data-dense layouts with clean typography (Inter font)
- Professional, enterprise-grade feel

### Frontend Pages
1. **Dashboard** - KPI overview, live conflict feed, department status, timeline
2. **Map** - 3D wireframe city mesh with conflict overlays, department filters
3. **Conflicts** - Table view of all conflicts, detail panels, resolution workflow
4. **Departments** - Department cards, planned works lists, agent status
5. **Notices** - Generated citizen notices, download links
6. **Agents** - Agent activity feed, reasoning traces, observability

### API Design
All services communicate through the API Gateway. The gateway exposes:
- `GET /api/departments` - List departments
- `GET /api/planned-works` - List planned works (filterable by dept)
- `GET /api/conflicts` - List detected conflicts
- `POST /api/conflicts/{id}/resolve` - Resolve a conflict
- `GET /api/mesh/{city}` - Get mesh data for a city
- `GET /api/notices` - List generated notices
- `GET /api/agents/activity` - Agent activity feed
- `GET /api/agents/traces/{id}` - Reasoning trace for an agent run
- `GET /api/events` - SSE stream for real-time updates
