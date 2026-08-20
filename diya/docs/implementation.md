# DIYA - Implementation Log

## What Has Been Built

### 1. Project Structure (Monorepo)
**What:** A monorepo containing 5 microservices, shared packages, synthetic data, Docker configs, and infrastructure-as-code.

**Why:** Microservices architecture allows independent scaling and deployment of each service. The monorepo keeps everything in one place for hackathon velocity while maintaining clean service boundaries.

**Purpose:** Each service has a single responsibility:
- `web` - User-facing dashboard and visualization
- `api-gateway` - Central routing, auth, request validation
- `agent-service` - AI agent orchestration via Google ADK
- `mesh-service` - GIS data processing and spatial analysis
- `notice-service` - Citizen notice artifact generation

---

### 2. Frontend Application (`apps/web`)
**What:** Next.js 14 application with App Router, TypeScript, Tailwind CSS, deck.gl, Framer Motion, and Recharts.

**Why:** Next.js provides SSR for fast initial loads, App Router for modern React patterns, and TypeScript for type safety. Tailwind enables rapid styling with a consistent design system.

**Purpose:** Provides the primary user interface for municipal coordinators and department planners to:
- View city-wide infrastructure work plans on a 3D wireframe map
- Detect and resolve cross-department conflicts
- Monitor AI agent activity and reasoning traces
- Download generated citizen notices

#### 2.1 Design System
**What:** Monochromatic black/white color palette with subtle animations.

**Why:** Professional, enterprise-grade aesthetic comparable to Palantir tools. Monochromatic scheme reduces visual noise and focuses attention on data. Subtle Framer Motion animations add polish without distraction.

**Color tokens:**
- Background: `#000000` to `#0a0a0a`
- Card surfaces: `#0a0a0a` to `#141414`
- Borders: `#1a1a1a` to `#222222`
- Text: `#ffffff` (primary), `#a0a0a0` (secondary), `#666666` (muted)
- Status: Red (conflict), Green (resolved), Amber (pending) -- used sparingly

#### 2.2 Layout Components
**What:** AppShell, Sidebar, TopBar

**Why:** Consistent navigation frame across all pages. Sidebar provides primary navigation with icon + label pattern. TopBar shows breadcrumbs, search, and user actions.

**Purpose:** Enterprise apps need a persistent navigation shell. The sidebar collapses to icons-only on smaller screens.

#### 2.3 Dashboard Page (`/dashboard`)
**What:** KPI metric cards, conflict timeline chart, live conflict feed, department status grid.

**Why:** The dashboard is the "command center" view for a municipal commissioner. Shows system health at a glance.

**Components:**
- `MetricCard` - Animated counter for key metrics (active conflicts, resolved, departments, planned works)
- `ConflictTimeline` - Recharts area chart showing conflicts over time
- `LiveFeed` - Real-time scrolling feed of agent actions and conflict events
- `DepartmentGrid` - Status cards for each department showing work counts and agent health

#### 2.4 Map Page (`/map`)
**What:** Full-screen 3D wireframe city mesh using deck.gl with conflict overlays.

**Why:** The core visual differentiator. Shows building footprints and road networks as extruded wireframe polygons on a dark basemap. Conflicts are highlighted with pulsing overlays. Department work zones are color-coded.

**Components:**
- `CityMesh` - deck.gl map with PolygonLayer (extruded, wireframe), PathLayer (roads), ScatterplotLayer (conflict points)
- `MapControls` - City selector (Mumbai/Delhi/custom upload), layer toggles, department filters
- `ConflictOverlay` - Pulsing markers on active conflict zones
- `MapLegend` - Legend for department colors and conflict status

#### 2.5 Conflicts Page (`/conflicts`)
**What:** Searchable/filterable table of all detected conflicts with detail panel and resolution workflow.

**Why:** Department planners need to see all conflicts affecting their work, filter by department/status/type, and take action (accept consolidated window, dismiss, escalate).

**Components:**
- `ConflictTable` - Sortable table with conflict ID, departments involved, overlap type, status, dates
- `ConflictDetail` - Slide-out panel showing full conflict details, affected works, proposed consolidated window, reasoning trace
- `ResolutionPanel` - Action buttons and form for resolving a conflict

#### 2.6 Departments Page (`/departments`)
**What:** Grid of department cards showing planned works, agent status, and identity scope.

**Why:** Provides per-department visibility into planned works and agent health. Also demonstrates Agent Identity scoping (which department can access what).

#### 2.7 Notices Page (`/notices`)
**What:** List of generated citizen notices with PDF/ICS download links.

**Why:** The "real action" proof point. Shows that the system produces tangible artifacts, not just dashboards. Each notice corresponds to a resolved conflict.

#### 2.8 Agents Page (`/agents`)
**What:** Agent activity feed, status indicators, and reasoning trace viewer.

**Why:** Demonstrates Agent Observability. Judges need to see the reasoning chain: why did the Coordinator flag these two projects? This page shows the full trace.

---

### 3. Mock Data Layer (`apps/web/src/lib/mock-data.ts`)
**What:** Comprehensive mock data for all entities: departments, planned works, conflicts, mesh edits, notices, agent activities.

**Why:** Allows full frontend development and demo without backend dependency. Data is realistic (real Mumbai/Delhi road names, actual department structures, plausible project types).

**Purpose:** De-risks the frontend build from backend timeline. The mock data layer is swappable with real API calls via a single configuration change.

---

### 4. Synthetic Data (`data/synthetic/`)
**What:** JSON seed files for Mumbai and Delhi with realistic department data, planned works, and pre-seeded conflicts.

**Why:** Judges discount toy data. These files use real OSM road names, actual Indian municipal department naming, and realistic project types (resurfacing, water main replacement, OFC laying).

---

### 5. Docker Configuration (`docker/`)
**What:** Docker Compose file orchestrating all 5 services + Dockerfiles for each service.

**Why:** Enables one-command local development (`docker compose up`) and mirrors the Cloud Run deployment target.

**Purpose:** Any reviewer can clone the repo and run the full stack locally without installing Python, Node, or any other dependencies.

---

### 6. Shared Types (`packages/shared/`)
**What:** TypeScript type definitions shared between frontend and any TypeScript services.

**Why:** Single source of truth for data shapes. Prevents type drift between frontend expectations and backend responses.

---

### 7. Performance & Responsiveness Fixes
**What:** Replaced Framer Motion staggered animations with CSS animations for list items, added responsive breakpoints across all pages, fixed SVG map scaling.

**Why:** Framer Motion was causing frame drops when rendering 10+ animated list items simultaneously. Each `motion.div` with a staggered delay creates a separate animation timeline, overloading the browser's compositor. CSS `@keyframes` animations are hardware-accelerated and don't cause the same overhead.

**Changes:**
- Dashboard components use `animate-slide-up` / `animate-fade-in` CSS classes instead of `motion.div`
- LiveFeed, ConflictTimeline, DepartmentGrid no longer use Framer Motion
- Sidebar auto-collapses below 1024px viewport width
- All pages use responsive `sm:` / `md:` / `lg:` / `xl:` breakpoints
- Map SVG uses `preserveAspectRatio="xMidYMid meet"` for proper scaling
- Conflict detail panel and Agent trace panel stack below content on mobile
- Search dropdown positions correctly on all screen sizes
- Bundle sizes reduced ~30% (agents page: 135kB -> 97.5kB)

---

### 8. Backend Services — Phase 2 (Scaffolded)
**What:** All 4 Python microservices fully scaffolded with working endpoints, mock data, CORS, proper response models, and documentation.

**API Gateway** (`apps/api-gateway`, port 8000):
- `GET /api/departments` — list/get departments
- `GET /api/planned-works` — filterable planned works
- `GET /api/conflicts` — filterable conflicts with full work objects
- `POST /api/conflicts/{id}/resolve` — resolve conflict, trigger notice agent
- `GET /api/mesh/{city}` — proxy to mesh service
- `GET /api/notices` — list generated notices
- `GET /api/agents/activity` — agent activity feed
- `GET /api/agents/traces/{id}` — reasoning traces
- `POST /api/complaints` — citizen complaint with Model Armor injection detection
- `GET /api/events` — SSE stream for real-time updates
- `GET /api/dashboard/metrics` — dashboard KPIs

**Mesh Service** (`apps/mesh-service`, port 8001):
- `GET /mesh/{city}` — full building/road geometry (consistent with frontend data)
- `POST /spatial/overlap` — geofence intersection analysis with distance calculation
- `GET /cities` — available city configurations

**Agent Service** (`apps/agent-service`, port 8002):
- `POST /agents/department/ingest` — trigger department feed normalization
- `POST /agents/coordinator/detect` — trigger conflict detection scan
- `POST /agents/coordinator/resolve` — resolve conflict with max-turn cap
- `GET /agents/traces/{id}` — full 5-step reasoning trace with timing
- `POST /agents/identity/verify` — demo Agent Identity scope check (GRANTED/DENIED)
- `GET /agents/status` — all agent statuses

**Notice Service** (`apps/notice-service`, port 8003):
- `POST /notices/generate` — generate ICS calendar file (working) + PDF placeholder
- `GET /notices/{id}/ics` — download ICS file
- `GET /notices/{id}/pdf` — download PDF (pending ReportLab implementation)

---

### 9. API Integration Layer — Phase 3
**What:** Centralized API client, data fetching hooks, loading skeletons, toast notifications, settings page, Terraform IaC, and development scripts.

**API Client** (`apps/web/src/lib/api.ts`):
- Centralized fetch wrapper with `USE_MOCK` flag for easy backend swap
- Functions for all endpoints: departments, planned works, conflicts, mesh, notices, agents, dashboard
- `submitComplaint()` with Model Armor integration
- `subscribeToEvents()` SSE client

**useApi Hook** (`apps/web/src/hooks/useApi.ts`):
- Generic data fetching hook with loading/error/data states
- Automatic refetch on dependency changes

**UI Utilities:**
- `Skeleton.tsx` — Loading states: MetricCardSkeleton, ConflictCardSkeleton, TableRowSkeleton, AgentActivitySkeleton, DashboardSkeleton
- `Toast.tsx` — Toast notification system with ToastProvider context, auto-dismiss, and 4 severity levels

**Settings Page** (`/settings`):
- General, Notifications, Security sections with toggle switches
- Infrastructure status display (GCP, Firestore, Agent Runtime, LLM)
- Governance stack visualization showing all 7 Enterprise Agent Platform pillars

**Infrastructure:**
- `infra/main.tf` — Full Terraform config: GCP APIs, Artifact Registry, Firestore, Cloud Storage, Pub/Sub with DLQ, Cloud Run services, IAM
- `scripts/setup.sh` — One-time project setup (npm deps, Python venvs, .env creation)
- `scripts/dev.sh` — Local dev runner (starts all 5 services with background processes)

---

### 10. Governance & Security — Phase 4
**What:** Dedicated governance page with interactive Agent Identity, Model Armor, Agent Gateway, and live demo capabilities. Added governance API endpoints.

**Why:** The "Fortified Enterprise Fleet" track requires demonstrating all 7 pillars of the Google Enterprise Agent Platform. This page provides a dedicated showcase for judges to see identity scoping, prompt injection defense, and the full request flow architecture.

**Governance Page** (`/governance`):
- **Agent Gateway tab** — Visual request flow architecture (6-step pipeline from citizen input to observability), Enterprise Agent Platform pillar cards (7 pillars with descriptions), runtime configuration display (max turns, timeout, rate limits, circuit breaker)
- **Agent Identity tab** — Per-department scope cards showing read/write/cross-dept access, Coordinator elevated scope with wildcard read, Identity verification log with GRANTED/DENIED results and scope details
- **Model Armor tab** — Threat detection log showing blocked/passed inputs, threat type classification (injection, jailbreak, exfiltration), armor statistics dashboard
- **Live Demo tab** — Interactive Model Armor tester with text input, quick-test buttons for safe/injection/jailbreak inputs, real-time scan results with severity display

**Governance API Endpoints** (added to `api-gateway`):
- `GET /api/governance/identity/verify` — Agent Identity scope verification
- `POST /api/governance/armor/scan` — Model Armor threat scanning with pattern classification
- `GET /api/governance/stats` — Governance dashboard statistics

**Sidebar Update:** Added "Governance" nav item with Shield icon between Agents and Settings.

---

## Architecture Decisions

### Decision 1: deck.gl over Three.js
deck.gl provides built-in geospatial layers (PolygonLayer, PathLayer) that natively handle lat/lng coordinates, GeoJSON, and map projections. Three.js would require manual coordinate transformation and custom geometry builders. For the "wireframe city mesh" requirement, deck.gl's `wireframe: true` option on PolygonLayer delivers the exact aesthetic with minimal code.

### Decision 2: SSE over WebSocket for real-time updates
Server-Sent Events are simpler to implement, natively supported by browsers, and sufficient for the one-directional data flow (server → client) this app needs. WebSocket would add complexity without benefit since the client never pushes data to the server in real time.

### Decision 3: FastAPI as API Gateway
FastAPI's auto-generated OpenAPI docs, Pydantic validation, and async support make it ideal for a hackathon. It's familiar from previous projects (CORTEX Lite) and provides a clean decoupling layer between the agent mesh and the frontend.

### Decision 4: Monochromatic design with surgical color
Pure black/white with status colors (red/green/amber) used only where semantically necessary. This creates the "data intelligence platform" feel (Palantir, Bloomberg Terminal) and avoids the "colorful SaaS dashboard" aesthetic that would undermine the enterprise positioning.
