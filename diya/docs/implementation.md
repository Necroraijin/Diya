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

### 8. Backend Services — Phase 2 (Built)

> The section below originally described the scaffolded version, where the
> endpoints returned hardcoded literals. Phase 2 replaced that with real
> implementations; §8b records what actually runs now.

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

### 8b. Backend Services — Phase 2 (what actually runs)

**Why the rewrite:** every service above returned literals. There was no
conflict-detection algorithm anywhere in the repo, the "generated" PDF was a
placeholder, the SSE stream was a synthetic heartbeat, and the seed data was
triplicated across the JSON files, the mesh service and the gateway — three
copies that had already drifted.

**`packages/core-py` — the shared package (new).** Installed editable into
every Python service (`pip install -e packages/core-py`):
- `models.py` — camelCase Pydantic models mirroring `apps/web/src/types/index.ts`
  exactly, so `.model_dump()` is directly consumable by the frontend.
- `geo.py` — haversine distance and geofence intersection.
- `conflict.py` — **the detection algorithm.** Geofence penetration (or a shared
  OSM `wayId`) qualifies a pair; date-range overlap or a repeat-dig inside the
  365-day window makes it a conflict; union-find groups pairs into multi-party
  conflicts; consolidation sequences the works deepest-excavation-first
  (sewage → water → telecom → roads) with a rolling 60% phase overlap. Savings
  are derived arithmetic, not constants.
- `seed.py` — `data/synthetic/*.json` is now the single source of truth.
- `events.py` — async event bus with bounded per-subscriber queues (drops
  oldest rather than stalling the publisher).
- `repository.py` — `Repository` ABC with in-memory and Firestore
  implementations; Firestore failures degrade to memory instead of 500ing.
  Re-detection preserves `resolved`/`dismissed` status across runs.
- `pubsub.py` — Pub/Sub publisher with a local no-op fallback and a DLQ.

**Gateway:** repository-backed, real upstream health probes, `POST
/api/conflicts/detect`, the resolve → notice-generation chain, artifact
streaming, `POST /api/ingest/{dept_id}`, governance stats derived from the real
activity log, and an SSE stream carrying genuine domain events
(`agent.activity`, `conflict.resolved`, `notice.generated`, `armor.blocked`).
CORS was `allow_origins=["*"]` with `allow_credentials=True` — an invalid
combination browsers reject; origins are now enumerated.

**Mesh service:** live Overpass fetch keyed by stable OSM way id, with a disk
cache and hand-digitised bundled fallback geometry so a dead Overpass never
breaks the demo (PRD §12 red flag #3). Overlap areas are computed with shapely
under a local equirectangular projection, so `intersection_area_m2` is real m².

**Notice service:** ReportLab produces a full municipal notice PDF (authority
header, closure meta table, affected area, sequence-of-works, departments,
public benefit, grievance channel) and `icalendar` produces a valid VCALENDAR
with one VEVENT per phase plus a −1 day alarm. Both carry the synthetic-data
disclaimer required by PRD §11. Artifacts persist to GCS when `GCS_BUCKET` is
set, otherwise to a local volume.

**Agent service:** `/agents/status` is derived from the seeded departments. The
orchestration endpoints now return **501** rather than fabricated success
payloads — a stub that lies about having run an agent is worse than one that
admits it has not been built. ADK wiring is Phase 3.

**Governance:** identity scoping had two implementations with disagreeing
parsers; there is now one (`api-gateway/governance.py`). Model Armor's
substring list flagged any complaint containing "database", "pretend" or "dan"
— "Dandekar Road" would have been a live false positive — and is now 13
word-boundary-anchored patterns that redact rather than discard, so the
legitimate part of a complaint survives.

**Verified end-to-end** with all four services up: detection independently
rediscovers both hand-authored seeded conflicts (`conf-001` 4-way critical,
`conf-002` 3-way critical); the PDF is a valid `%PDF-1.4` with all text
confirmed via pypdf; the ICS parses as a valid VCALENDAR; resolve → notice →
download all return 200 and a second resolve returns 409; the mesh falls back
correctly with Overpass pointed at an unreachable host; identity
GRANTED/DENIED/wildcard all behave; ingest publishes in local mode.

> **Note for the demo script:** consolidation savings are now derived from the
> works' own budgets and differ from the figures hardcoded in `mock-data.ts`
> (`conf-001` derives ₹1.44 Cr against the ₹3.2 Cr previously shown). The
> frontend still reads mock data — wiring it to the live gateway is Phase 5 —
> so the two disagree until then.

---

### 8c. Agent Layer — Phase 3

**What:** the ADK fleet from PRD §6, its orchestration from §6.4, and the
Memory Bank from §6.2, in `apps/agent-service/`.

**`agents.py` — the fleet.** One `LlmAgent` per department (built from the
seeded department list, so adding a department adds an agent), a Coordinator,
and a Citizen Notice Agent, assembled as
`SequentialAgent[ParallelAgent[dept×4], coordinator, notice]`. The department
agents are independent, so they run concurrently; the Coordinator cannot start
until every feed is in, so that edge is sequential. `GET /agents/topology`
returns the tree built from the live agent objects, which means the
architecture diagram cannot drift from the code it describes.

Each agent is handed only the tools its Identity can use. A Department Agent
has no tool that reads a peer, and carries `disallow_transfer_to_peers=True`
— so the scope boundary holds structurally as well as at the gateway.

**`tools.py` — gateway-mediated, identity-checked.** No agent opens its own
Firestore handle; every tool goes through the API gateway, and every tool
verifies its caller's scope before the read. That is the Agent Gateway
mediation of PRD §5, and it makes the cross-department denial real rather than
narrated: `read_all_planned_works` under a department identity raises
`ScopeDenied`, and the refusal is logged to the activity feed the governance
page renders.

**`memory.py` — Memory Bank.** Cross-session recollection keyed by conflict id:
first seen, times surfaced, last outcome. Flushed on every write through a
temp-file rename, because the demo restarts services and a memory that only
persisted on clean shutdown would not survive that. Backed by Vertex Agent
Engine when `MEMORY_BANK` is set, by a local JSON file otherwise.

**`orchestrator.py` — two runners, one tool set.** `run_adk` drives the real
tree through an ADK `Runner`; `run_deterministic` calls the same tools in the
same order with no model. Both are honest about which ran, and an ADK failure
falls through to the deterministic path with the cause attached rather than
being presented as an agent run.

**Why a deterministic path at all.** The overlap distances, phase ordering and
rupee savings come from `diya_core.conflict` on *both* paths — the model
sequences tools and narrates, it does not do arithmetic. The agent instructions
forbid it explicitly. An LLM inventing a number a judge then checks is a worse
outcome than no LLM in the loop, and this way the pipeline is verifiable
without credentials.

**Three bugs found by running it:**
- The max-turn cap counted department ingestion against the Coordinator's
  budget, so with 4 departments the Coordinator was starved before it could
  propose a single window. The cap now applies to the stage PRD red flag #9 is
  actually about.
- The Citizen Notice Agent was denied `conflicts/{id}` — `governance.py` only
  modelled department scopes, so a functional agent got parsed as a department
  and refused the two collections it exists to touch. Non-department scopes now
  declare their grants explicitly (`FUNCTIONAL_SCOPES`).
- ADK runs sub-agents in a `TaskGroup`, so a missing credential surfaced as
  "ExceptionGroup: 4 sub-exceptions". Unwrapped, it now reads "No API key was
  provided", which is the thing a person can act on.

**Verified end-to-end**, all four services up, no GCP credentials:
- Full run: 8 department tool calls (13 records), cross-department read,
  detection finding `conf-001` (4 works, 4 phases) and `conf-002` (3 works,
  3 phases), then two notices — PDF 4,237 bytes `%PDF-1.4`, ICS 2,531 bytes
  valid `VCALENDAR`, both downloadable through the gateway.
- Memory: second run reports "Seen before: first surfaced …, 2 time(s)";
  after resolution a third run skips both with "already resolved; not
  re-flagged"; entries survive an agent-service restart.
- Identity: the full matrix — notice/conflicts GRANTED, notice/departments
  DENIED, coordinator wildcard GRANTED, department cross-read DENIED,
  department own-write GRANTED, malformed identity DENIED.
- Turn cap: at `AGENT_MAX_TURNS=3` the run truncates cleanly, marking the
  un-run steps skipped rather than failing.
- ADK path: the tree builds under `google-adk` 2.7.1; forced without a
  backend it reports the real credential error and falls through.

---

### 8d. Governance & Security — Phase 4

**What:** three new modules in `apps/api-gateway/` — `gateway_policy.py`,
`observability.py`, `registry.py` — plus the middleware and routes that apply
them.

**Agent Gateway (`gateway_policy.py`).** Phase 2 reported a rate limit, a
timeout and a circuit-breaker threshold on `/api/governance/stats` and enforced
none of them. Now:
- **Rate limiting** is a token bucket keyed by calling identity
  (`X-Agent-Identity`, else `agent_id`, else peer address), so a burst is
  allowed but a sustained flood is not, and one looping agent is throttled
  without affecting the rest of the fleet. Applied to the agent-facing and
  citizen surfaces only — throttling a coordinator's dashboard refresh buys
  nothing.
- **Circuit breakers**, one per upstream, closed → open → half-open. A 4xx from
  a healthy service does *not* count toward the breaker; only transport errors
  and 5xx do, otherwise one bad request id would trip the circuit for everyone.
- **Timeouts** on every upstream call.

State is per-process, which is honest for one replica; behind a load balancer
the limits would be per-replica rather than global, and that is noted in the
module.

**Agent Observability (`observability.py`).** A span tree per request — id,
parent, name, attributes, duration, status — in a bounded ring buffer, with
optional Cloud Trace export under `OTEL_EXPORT=cloudtrace`. The buffer is the
primary surface either way, because Cloud Trace is unreachable in the offline
demo and an observability story that only works with credentials is not one.
Every response carries `X-Trace-Id`, so a specific slow call can be looked up
by the exact request that made it. Bounded on purpose: an unbounded trace
buffer in a long-running gateway is a memory leak with a nice name.

**Agent Registry (`registry.py`).** The register is derived from the same seed
the fleet is built from, then **reconciled against the running agent-service**.
`GET /api/registry` reports `in_sync`, `drift` (naming what is only in one
side), or `unknown` when the fleet cannot be reached — never agreement, because
"I could not check" and "they match" are different answers and only one is
reassuring.

**One bug found by testing:** the artifact download route called the notice
service directly, bypassing the breaker — so with the notice service dead, every
PDF request still hung for ~2.6s instead of failing fast. It now goes through
`_call_upstream` like everything else.

**Verified against real traffic:**
- Rate limit at 5/min: `200 200 200 200 200 429 429 429` for one identity, while
  a second identity and the unpoliced dashboard reads both stayed 200.
- Circuit breaker at threshold 3 with the notice service killed: three ~2.6s
  failures, then fail-fast at ~305ms, breaker `open` with `trips: 1`. After the
  cooldown it admitted exactly one probe, which re-opened it while the service
  was still down, then closed cleanly once the service returned.
- Traces: a resolve request produced a two-span tree —
  `POST /api/conflicts/conf-001/resolve` 286.96ms with a nested
  `upstream.notice-service` 284.3ms child, which is the "where did the time go"
  answer.
- Registry: `in_sync` against the live ADK tree; `unknown` with agent-service
  down; and against a doctored topology it correctly reported
  `registeredButNotRunning: [sewage_department_agent]` and
  `runningButNotRegistered: [ghost_department_agent]`.

---

### 9. API Integration Layer — Phase 3
**What:** Centralized API client, data fetching hooks, loading skeletons, toast notifications, settings page, Terraform IaC, and development scripts.

**API Client** (`apps/web/src/lib/api.ts`):
- Centralized fetch wrapper. (The `USE_MOCK` flag was dead — nothing read it —
  and was removed in Phase 2; pages import from `mock-data.ts` directly, and
  connecting them to these functions is Phase 5.)
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
