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

### Phase 2: Backend Services (Day 3-4) — complete
- [x] FastAPI gateway with all endpoints (26 routes, repository-backed)
- [x] Firestore schema and connection (`FirestoreRepository`, degrades to memory)
- [x] Pub/Sub topic setup and ingestion pipeline (`POST /api/ingest/{dept_id}`, DLQ, local no-op publisher)
- [x] Mesh service: OSM data fetch, spatial processing (Overpass + disk cache + bundled fallback; shapely areas in real m²)
- [x] Notice service: PDF/ICS generation (ReportLab + icalendar, GCS-or-local storage)
- [x] SSE real-time updates (`/api/events`, backed by a real domain event bus)

Also landed in this phase, because nothing above worked without it:
- [x] `packages/core-py` (`diya-core`) — shared models, geo maths, seed loader, event bus, repositories, Pub/Sub
- [x] **Deterministic conflict detection** (`diya_core.conflict`) — geofence penetration + date-overlap + union-find grouping + depth-ordered consolidation. It independently rediscovers both hand-authored seeded conflicts.
- [x] Governance consolidated into one module (identity scoping was previously implemented twice with disagreeing parsers)

WebSocket was not built: SSE covers every push the UI needs and the browser
never writes upstream over the same channel.

### Phase 3: Agent Layer (Day 5-7) — complete
- [x] ADK agent scaffolding (`google-adk` 2.7.1; the tree builds and is served at `GET /agents/topology`)
- [x] Department Agents (normalize feeds) — one `LlmAgent` per department, each holding only its own two tools
- [x] Coordinator Agent (conflict detection) — the one identity with cross-department read scope
- [x] Citizen Notice Agent (artifact generation) — conditional leg, runs only on resolution
- [x] Agent orchestration: `ParallelAgent(departments) -> Coordinator -> Notice` inside a `SequentialAgent`
- [x] Memory Bank for cross-session state — a re-run recognises a conflict it has already surfaced and does not re-flag one already signed off
- [x] Max-turn cap on the Coordinator (PRD red flag #9), enforced by the runner rather than by instruction

**Execution has two paths over one tool set.** With a Gemini backend configured
(`GOOGLE_API_KEY`, or `GOOGLE_GENAI_USE_VERTEXAI` with a real project) the ADK
tree runs. Without one, the same tools execute in the same order
deterministically. Both report which path ran — `execution_mode` on `/health`
and `mode` on every run — and if the ADK path fails mid-run the response says
so verbatim rather than quietly presenting the fallback as an agent run.

This is not a stub standing in for missing work: the arithmetic lives in
`diya_core.conflict` on **both** paths, so the LLM adds narration, not numbers.
An agent inventing an overlap distance or a rupee saving is the fastest way to
lose a judge who checks one.

Not yet done, and needing a GCP project rather than more code: deploying the
fleet to Agent Runtime, and pointing `MEMORY_BANK` at a real Vertex Agent
Engine instead of the local file.

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
