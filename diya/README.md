# DIYA — Dig Infrastructure Yielding Alignment

> Preventing municipal departments from digging up the same road repeatedly.

Four departments plan work on the same 200 m of SV Road, Andheri West. None of
them knows about the other three. The road is opened, resurfaced, opened again
for fibre, resurfaced, opened again for a water main. DIYA is a fleet of agents
that reads every department's plan, finds the collisions, proposes one
consolidated dig window in the correct excavation order, and issues the citizen
notice — as a real PDF and a real calendar file.

Built for the All Things Agentic Hackathon 2026 (Google), **Fortified Enterprise
Fleet** track.

---

## Architecture

```
                          ┌──────────────────────────┐
                          │  Next.js 14 dashboard    │
                          │  (browser)               │
                          └───────────┬──────────────┘
                                      │  REST + SSE
                                      ▼
   ┌───────────────────────────────────────────────────────────────┐
   │                    API GATEWAY  (FastAPI, :8000)              │
   │                                                               │
   │   Agent Gateway     rate limit · timeout · circuit breaker    │
   │   Agent Identity    per-department + functional scope check   │
   │   Model Armor       13 anchored patterns on citizen input     │
   │   Observability     span tree per request, X-Trace-Id         │
   │   Agent Registry    declared fleet reconciled against live    │
   └───┬───────────────────┬───────────────────┬───────────────────┘
       │                   │                   │
       │ every agent tool call goes over HTTP through the gateway.
       │ agents hold no store credentials of their own.
       │                   │                   │
       ▼                   ▼                   ▼
 ┌───────────────┐  ┌──────────────┐  ┌────────────────┐
 │ agent-service │  │ mesh-service │  │ notice-service │
 │    :8002      │  │    :8001     │  │     :8003      │
 │  Google ADK   │  │ Overpass/OSM │  │ ReportLab PDF  │
 │               │  │ Shapely      │  │ icalendar ICS  │
 └───────┬───────┘  └──────────────┘  └────────────────┘
         │
         │  SequentialAgent
         │  ┌────────────────────────────────────────────┐
         │  │ ParallelAgent                              │
         └─▶│  ├── roads_department_agent                │  scope: departments/dept-roads/**
            │  ├── water_department_agent                │  scope: departments/dept-water/**
            │  ├── telecom_department_agent              │  ← cross-department read DENIED
            │  └── sewage_department_agent               │
            ├────────────────────────────────────────────┤
            │ coordinator_agent                          │  scope: departments/**  (the one
            │   detect · sequence by depth · cost        │   elevated identity in the fleet)
            │   Memory Bank: has this been seen before?  │
            ├────────────────────────────────────────────┤
            │ citizen_notice_agent                       │  scope: conflicts:read, notices:write
            │   runs only on resolution → PDF + ICS      │
            └────────────────────────────────────────────┘

 Shared package `packages/core-py` (diya-core) holds the models, the geo maths
 and — critically — the conflict arithmetic. Both execution paths call it, so
 the LLM narrates numbers it did not invent.
```

### Two execution paths, one tool set

With a Gemini backend configured (`GOOGLE_API_KEY`, or `GOOGLE_GENAI_USE_VERTEXAI`
with a real project) the ADK tree runs for real. Without one, the *same tools*
execute in the same order deterministically. Both report which path ran —
`execution_mode` on `/health`, `mode` on every run — and an ADK failure mid-run
is reported verbatim rather than being quietly presented as an agent run.

The overlap distances, phase ordering and rupee savings come from
`diya_core.conflict` on both paths. An agent that invents an overlap distance is
the fastest way to lose a judge who checks one.

---

## Quick start

Requires Python 3.11+ and Node 18+. No GCP account needed — the whole stack runs
offline against bundled synthetic data.

```bash
# 1. Python deps (installs the shared diya-core package editable)
./scripts/setup.sh

# 2. Node deps (npm workspace — installs to the repo root)
npm install

# 3. All four Python services
./scripts/dev.sh          # :8000 gateway, :8001 mesh, :8002 agents, :8003 notices

# 4. The dashboard
npm run dev               # http://localhost:3000
```

Or everything in containers:

```bash
docker compose -f docker/docker-compose.yml up --build
```

### Verify it is actually live

```bash
curl localhost:8000/health          # every upstream probed, not asserted
curl localhost:8000/api/conflicts   # 2 conflicts rediscovered from the seed
```

The dashboard's top bar reads **Live — API Gateway** when it is talking to the
backend and **Demo data — gateway offline** when it is not. Stop the gateway and
watch it flip: the UI falls back to seeded fixtures but never pretends they are
live.

---

## The demo path

1. **Dashboard** — 2 conflicts across 13 planned works and 4 departments.
2. **Conflicts** → `conf-001`. Four departments, one 200 m stretch of SV Road.
   The reasoning trace is derived: geofence penetration in metres, date overlap,
   depth-ordered sequencing (storm drain → water main → OFC → resurfacing,
   because surface work must never be re-opened), and ₹1.44 Cr of avoided
   mobilisation and restoration.
3. **Resolve & Notify** — one click. The conflict is marked resolved *and* the
   Citizen Notice Agent generates a real PDF and ICS, downloadable from the
   Notices page.
4. **Governance → Live Demo** — paste a prompt injection into the citizen
   complaint box; Model Armor blocks it and it appears in the activity feed.
5. **Governance → Agent Identity** — the water agent reading `departments/**` is
   refused: *"Scope violation: the water agent holds no cross-department read
   scope. Only the Coordinator does."*
6. **Agents** — the span tree for the resolution, with real timings.

---

## Governance (the track requirement)

| Control | Where | What it actually does |
|---|---|---|
| Agent Identity | `api-gateway/governance.py` | One parser. Department scopes and functional scopes, checked on **every** tool call, not at startup. |
| Agent Gateway | `api-gateway/gateway_policy.py` | Token-bucket rate limit per caller identity, per-call timeouts, per-upstream circuit breaker. Enforced, and `/api/governance/stats` reports live state rather than echoing env vars. |
| Model Armor | `api-gateway/governance.py` | 13 anchored patterns on the citizen input surface. Redacts rather than discards, so a real complaint containing one bad sentence still gets filed. |
| Memory Bank | `agent-service/memory.py` | Cross-session recollection. A re-run recognises a conflict it has surfaced before and does not re-flag one already signed off. Local JSON, or Vertex Agent Engine when `MEMORY_BANK` is set. |
| Observability | `api-gateway/observability.py` | Span tree per request, `X-Trace-Id` on every response, optional Cloud Trace export. Bounded ring buffer — an unbounded trace buffer is a memory leak with a nice name. |
| Agent Registry | `api-gateway/registry.py` | The declared fleet is **reconciled** against the running agent tree. Reports `in_sync` / `drift` / `unknown`; "I could not check" is never reported as agreement. |

---

## Layout

```
diya/
├── apps/
│   ├── web/              Next.js 14 dashboard (TypeScript, Tailwind, SVG mesh)
│   ├── api-gateway/      FastAPI gateway + all governance controls
│   ├── agent-service/    Google ADK agent fleet + Memory Bank
│   ├── mesh-service/     Overpass/OSM fetch, Shapely overlap geometry
│   └── notice-service/   ReportLab PDF + icalendar ICS generation
├── packages/core-py/     diya-core: models, geo maths, conflict detection, events
├── data/synthetic/       Seeded Mumbai + Delhi departments and planned works
├── docker/               Compose + per-service Dockerfiles
├── infra/                GCP Terraform
└── docs/                 plan.md, implementation.md
```

## Configuration

Everything below has a working offline default; set them only to go further.

| Variable | Default | Effect |
|---|---|---|
| `DIYA_STORE` | `memory` | `firestore` to persist |
| `GOOGLE_API_KEY` | — | Set to run the real ADK/Gemini path |
| `MEMORY_BANK` | — | Vertex Agent Engine id instead of local JSON |
| `OTEL_EXPORT` | — | `cloudtrace` to export spans |
| `AGENT_RATE_LIMIT` | `100` | Requests/min per caller identity |
| `AGENT_CIRCUIT_BREAKER` | `5` | Upstream failures before the circuit opens |
| `AGENT_MAX_TURNS` | `10` | Coordinator negotiation cap |

## Data

All department data is **synthetic**. It uses real OSM road names and realistic
Indian municipal department naming, but represents no actual government record
or citizen.

## License

MIT
