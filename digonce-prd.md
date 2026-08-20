# Diya — Multi-Agent Infrastructure Conflict Resolution System
### Product Requirements Document & System Architecture
**Author:** Sumit · **Prepared for:** All Things Agentic Hackathon 2026 (Google) · **Track:** Fortified Enterprise Fleet
**Deadline:** Aug 31, 2026, 5:00pm PDT — **read the timezone flag in §12 before you plan your final day**
**Status:** v1.0 — working name "Diya" is a placeholder, rename freely

---

## 1. Executive Summary

Diya is a multi-agent system that prevents the single most common failure in municipal infrastructure delivery: departments digging up the same road repeatedly because nobody cross-checks plans before work starts. A fleet of department-scoped agents (Roads, Water, Telecom, Sewage) ingest each department's planned works, a Coordinator Agent detects spatial/temporal conflicts across them, and the resolution is rendered live onto an editable 3D wireframe city mesh — plus a real downloadable citizen notice, so the output is an artifact a government office could actually use, not just a dashboard.

This is deliberately the **narrow, real slice** of a much larger "AI city planning platform" vision — built to be demoable end-to-end in 12 days, not a proof-of-concept sketch of the whole idea.

---

## 2. Problem & Users

**Problem:** Municipal departments plan and execute infrastructure work in silos. A road resurfaced in March gets dug up again in June by the water department, then again in September by a telecom operator laying fiber — same stretch, three closures, three citizen complaints, three budgets, avoidable with five minutes of cross-department visibility that currently doesn't exist anywhere in the workflow.

**Primary users:**
- **Ward Engineer / Department Planner** — submits their department's planned works, receives conflict flags before committing a budget line
- **Municipal Commissioner / Coordination Office** — needs a single view across all departments to approve consolidated "dig once" windows
- **Citizens** — receive one clear notice about one consolidated closure instead of three separate ones

**Non-users (explicitly out of scope):** contractors, procurement/tendering systems, real-time construction crews. Don't let the demo scope creep toward them.

---

## 3. Scope Boundary — What We Are and Are Not Building

This is the most important section in this document. A senior architect's first job here is saying no.

**In scope for the hackathon build:**
- 3–4 synthetic department data feeds (realistic, not toy data — see §11)
- Department Agents + Coordinator Agent + Citizen Notice Agent, built on ADK
- Conflict detection logic (spatial overlap + temporal window overlap)
- 3D wireframe mesh visualization of one real, bounded city area (a single ward or ~1–2 km² zone, not a whole city)
- Agent-driven live edits to the mesh (agent flags/moves/highlights elements)
- Governance layer: Agent Identity scoping, Agent Gateway + Model Armor on one concrete attack surface (citizen-submitted complaint text), Memory Bank for cross-session conflict state, Observability trace on the reasoning chain
- One real output artifact: a generated public-notice PDF/ICS file the Citizen Notice Agent actually produces

**Explicitly out of scope — do not build these, even if there's spare time:**
- Photorealistic 3D rendering of "what construction will look like" (this was correctly cut earlier — stay cut)
- Whole-city coverage — one ward is enough to prove the pattern
- Real integration with an actual municipal system or real citizen data
- Manual human click-and-drag mesh editing as a core feature — nice-to-have, not what's judged (see §12, red flag #6)
- A generalized "AI city planner" — that's the future-roadmap slide, not the build

---

## 4. Track & Judging Alignment

**Track: Fortified Enterprise Fleet** ($20,000, plus this project is a credible Grand Prize / Best Architectural Design contender given the governance depth available).

| Judging criterion | Weight | How this project earns it |
|---|---|---|
| Innovation & Operational Utility | 40% | Agents take real action (conflict resolution + generated notice), not just chat; solves a specific, named, real problem |
| Architectural Discipline & Tech Stack | 30% | Uses managed Gemini Enterprise Agent Platform pillars (Registry, Runtime, Identity, Gateway, Model Armor, Memory Bank, Observability) instead of hand-rolling governance — this is the single biggest scoring lever available and it's mostly configuration, not custom code |
| Demo & Production Readiness | 30% | Live reasoning trace, real GCP console proof, clean repo + README, architecture diagram |

Track-specific requirement check: the Fortified Enterprise Fleet brief explicitly asks for Registry, Runtime, Memory Bank, Identity, Gateway, Model Armor, and Observability. Don't treat these as optional flavor — a submission that skips visibly demonstrating 4+ of these will read as a relabeled Taskmaster entry and lose the track's biggest differentiator.

---

## 5. System Architecture

```
                     ┌─────────────────────────────────────────┐
                     │        Gemini Enterprise Agent Platform   │
                     │                                           │
  Dept data feeds ──▶│  ┌────────────┐  ┌────────────┐          │
  (synthetic, per     │  │ Roads Agent│  │ Water Agent│  ...     │
   department)        │  └─────┬──────┘  └─────┬──────┘          │
                     │        │                │                 │
                     │        └───────┬────────┘                 │
                     │                ▼                          │
                     │        ┌───────────────┐                  │
                     │        │ Coordinator    │◀── Memory Bank   │
                     │        │ Agent (conflict│    (cross-session│
                     │        │ detection)     │     resolved     │
                     │        └───────┬───────┘     conflicts)    │
                     │                ▼                          │
                     │        ┌───────────────┐                  │
                     │        │ Citizen Notice │                  │
                     │        │ Agent          │                  │
                     │        └───────┬───────┘                  │
                     │                │                          │
                     │  Agent Identity + Agent Gateway + Model    │
                     │  Armor wrap every agent-to-tool call        │
                     │  Agent Observability traces every hop       │
                     └────────────────┼──────────────────────────┘
                                      │ (structured JSON: conflict
                                      │  records, mesh edit ops,
                                      │  notice artifact URL)
                                      ▼
                     ┌─────────────────────────────────────────┐
                     │  Backend API (FastAPI on Cloud Run)       │
                     │  — Firestore (state) — Pub/Sub (ingest)   │
                     │  — Cloud Storage (OSM cache, notices)     │
                     └────────────────┬──────────────────────────┘
                                      ▼
                     ┌─────────────────────────────────────────┐
                     │  Frontend (Next.js + deck.gl/Three.js)    │
                     │  Wireframe city mesh, live agent edits,   │
                     │  timeline scrubber, conflict overlay      │
                     └─────────────────────────────────────────┘
```

**Design principle:** the agent mesh does not talk to the frontend directly. Everything flows through a thin FastAPI layer that persists state to Firestore and pushes updates over Server-Sent Events (SSE) or WebSocket to the frontend. This keeps the agent layer swappable — if Agent Platform access is delayed (see red flag #2), you can point the same FastAPI layer at agents running on plain Cloud Run without touching the frontend at all.

---

## 6. Agent Specifications

### 6.1 Department Agents (Roads, Water, Telecom, Sewage — 3–4 instances of one agent type, differently scoped)
- **Role:** normalize that department's planned-works records into a common schema
- **Input:** raw department feed (synthetic JSON seeded per §11)
- **Output:** normalized `PlannedWork` records (see §7)
- **Tools:** `read_department_feed`, `write_normalized_record`
- **Identity scope:** each instance's Agent Identity can only read its own department's Firestore collection — this is your cleanest zero-trust demo moment; show a denied cross-department read attempt on camera
- **Model:** Gemini 3.5 Flash, low temperature, structured output (JSON schema-constrained)

### 6.2 Coordinator Agent
- **Role:** cross-reference all normalized `PlannedWork` records, detect spatial (geofence overlap) + temporal (date window overlap) conflicts, propose a consolidated window
- **Input:** all `PlannedWork` records via Agent Gateway-mediated reads (its Identity is the only one with cross-department read scope — call this out explicitly as the governance design decision)
- **Output:** `ConflictRecord` with proposed consolidated window + reasoning trace
- **Memory:** Memory Bank stores which conflicts were already surfaced/resolved, so re-runs don't re-flag stale conflicts — this is the literal "persistent, secure cross-session context over extended timelines" requirement, don't skip wiring it in
- **Guardrail:** max-turn / loop cap on any negotiation logic between departments (see red flag #9 — this agent is the one most likely to loop)

### 6.3 Citizen Notice Agent
- **Role:** once a `ConflictRecord` is marked resolved, generate a real artifact: a public works notice (PDF) and a calendar file (ICS) for the consolidated closure window
- **Output:** files written to Cloud Storage, URL returned to frontend — **this is your "real action" proof point for the 40%-weighted Innovation & Operational Utility criterion**
- **Tools:** `generate_pdf_notice`, `generate_ics`, `write_to_storage`

### 6.4 Orchestration pattern (ADK)
Sequential handoff: Department Agents run in parallel (ADK `ParallelAgent`) → results feed a `SequentialAgent` step into the Coordinator → conditional transfer to Citizen Notice Agent only when a conflict resolves to "consolidated." Keep this linear and legible — a judge should be able to read the orchestration and understand it in one glance at the architecture diagram, which itself is a submission requirement.

---

## 7. Data Model (Firestore collections)

```
departments/{deptId}
  name, agentIdentityId, feedSource

planned_works/{workId}
  deptId, title, location: {lat, lng, wayId (OSM)}, geofenceRadius,
  startDate, endDate, workType, status

conflicts/{conflictId}
  workIds: [...], overlapType: spatial|temporal|both,
  proposedWindow: {start, end}, status: detected|resolved|dismissed,
  reasoningTrace, resolvedAt

mesh_edits/{editId}
  targetWayId or targetBuildingId, editType: highlight|reroute|flag,
  color, conflictId (ref), issuedByAgent, timestamp

notices/{noticeId}
  conflictId (ref), pdfUrl, icsUrl, generatedAt
```

---

## 8. GIS Mesh Subsystem

1. **Ingestion:** Overpass API query for the chosen ward/zone → building footprints (ways/polygons) + road network. Cache raw response in Cloud Storage — Overpass has rate limits, don't hit it live during the demo.
2. **Mesh schema:** each OSM way/building becomes an addressable object with a stable ID, so agents can reference `wayId: 48213...` in a `mesh_edits` record rather than emitting raw geometry.
3. **Rendering:** deck.gl `PolygonLayer` (extruded, wireframe style — dark background, thin glowing edges, semi-transparent fill) reading `planned_works` + `mesh_edits` live via SSE.
4. **Agent-driven edits, not user-driven:** the demo moment is the Coordinator Agent's decision appearing on the mesh in real time (a road segment turning amber, then green once resolved) — this is far more convincing on camera than a human dragging a marker, and it's a fraction of the engineering cost. Manual editing stays a stretch goal only.

---

## 9. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| LLM | Gemini 3.5 Flash via Vertex AI | Hackathon mandatory requirement |
| Agent framework | Google ADK (Python) | Mandatory framework requirement; native fit with Agent Platform's Build pillar |
| Agent deployment | Agent Runtime (Gemini Enterprise Agent Platform) | Matches "long-running, asynchronous background execution" from the track description almost verbatim; auto-registers to Agent Registry |
| Governance | Agent Identity, Agent Gateway, Model Armor | Direct, mostly-configuration path to the track's governance requirements — see red flag #1 |
| Cross-session memory | Memory Bank | Required by the track's own spec, purpose-built for exactly this need |
| Observability | Agent Observability / Cloud Trace | Reasoning-chain proof for the demo video |
| Structured state | Firestore | Familiar to you already (used in CORTEX Lite); native GCP; works cleanly with Agent Runtime |
| Async ingestion | Pub/Sub | Satisfies "handle heavy lifting... asynchronously" from the hackathon's own framing; required GCP infra service checkbox |
| Backend API | FastAPI on Cloud Run | Familiar, fast to stand up, decouples agent layer from frontend |
| GIS source data | OpenStreetMap (Overpass API) | Free, sufficient building/road coverage for a bounded demo zone |
| Frontend rendering | Next.js + deck.gl (fallback: Three.js) | deck.gl has extruded-polygon support out of the box, less custom shader work than raw Three.js |
| File artifacts | Cloud Storage | PDF/ICS notice hosting |
| Optional bonus | Veo | Generate a short "future vision" b-roll clip for the demo video intro — cheap way to satisfy the bonus "integrate Gemma/Veo/Lyria" checkbox without touching core architecture |

---

## 10. Non-Functional / Governance Mapping

- **Agent Identity:** one identity per Department Agent + one for the Coordinator; least-privilege Firestore access enforced at the identity level, not in application code
- **Agent Gateway + Model Armor:** placed in front of the one real external-input surface in this system — a citizen complaint text field feeding into `planned_works` metadata — screening for prompt injection before it reaches any agent. This is a legitimate, narrow, demoable security story rather than a vague "we have security" claim
- **Agent Observability:** every Coordinator decision should have a visible reasoning trace pulled up on camera during the demo — "why did it flag these two projects" is a concrete, judge-legible moment
- **Failure handling:** explicit max-turn caps on the Coordinator's negotiation logic (see red flag #9); Pub/Sub dead-letter topic for malformed department feed messages instead of silent drops

---

## 11. Data Credibility Requirement

Judges will discount anything that reads as obviously fake. Invest real time making the seed dataset plausible:
- Use actual OSM road names and ward boundaries for your chosen zone rather than "Road A / Road B"
- Give departments realistic Indian-municipal naming (e.g., actual department structures used by Indian ULBs) and realistic project types (resurfacing, water line replacement, OFC laying)
- Keep the dataset explicitly labeled as synthetic/demo data in the README and video narration — don't imply a real government partnership or real citizen data, which would be both inaccurate and a genuine problem if judges follow up

---

## 12. Red Flags — Senior Architect Risk Register

1. **Enterprise-pillar scope trap.** The Fortified Enterprise Fleet checklist has 7 named components. Attempting to hand-build all 7 from scratch in 12 days fails. Mitigation: lean entirely on the managed Gemini Enterprise Agent Platform (§9) — most of the governance story becomes configuration, not code.
2. **Platform maturity/access risk.** Gemini Enterprise Agent Platform components (Agent Runtime, Registry, Identity, Gateway) appear to be very recently GA'd — expect possible quota approval delays, regional availability gaps, or rough documentation edges. **Do a Day 1 spike**: provision access, deploy a trivial "hello world" ADK agent to Agent Runtime, confirm it actually works in your GCP project before the architecture depends on it. Fallback plan: same ADK agents self-hosted on Cloud Run with hand-rolled IAM scoping if platform access isn't usable in time — keep this fallback path in your back pocket, don't discover you need it on day 9.
3. **OSM data completeness for your target zone is unverified.** Check actual coverage for your chosen city/ward before committing — Overpass data quality varies significantly by area in India. Fallback: hand-pick a small, well-mapped zone, or manually digitize ~30-50 buildings if the auto-pull is too sparse. Don't let live data quality be a demo-day risk.
4. **Data credibility.** See §11 — generic placeholder data reads as a toy project, not a government tool.
5. **Scope creep back toward photorealism.** This was correctly cut in an earlier conversation. Flagging again because it's the single most tempting thing to add back in "just a little" — resist it. Wireframe mesh only.
6. **"Real action" requirement.** The track wants agents that act, not just detect-and-display. If the build stops at "conflict shown on a dashboard," it under-delivers on the highest-weighted criterion (40%, Innovation & Operational Utility). The Citizen Notice Agent's generated PDF/ICS is the fix — don't cut it under time pressure, it's not a nice-to-have, it's the proof of "action."
7. **Track-fit dilution.** This idea also fits "Taskmaster." If the governance layer (Identity/Gateway/Model Armor/Registry) doesn't show up *visibly* in the demo — not just exist in the code — the track choice doesn't pay off relative to the effort spent. Plan at least 2 explicit on-camera governance moments (a denied cross-department read; a blocked prompt-injection attempt).
8. **Solo-build surface area.** 12 days solo, including video, README, architecture diagram, deploy, and optional blog post, is already full. De-scope manual mesh editing (§3, §8) — it's the first thing to cut if you're behind on day 8.
9. **Runaway agent loops.** The Coordinator reassigning a conflict back and forth between two Department Agents is a realistic failure mode judges will probe for ("how do you handle failures" is explicitly in the rubric). Hard-code max-turn caps now, not as an afterthought.
10. **Cost control.** Set a Cloud Billing budget alert on day 1. Multi-agent Gemini calls + Agent Runtime + Maps/OSM calls can run up faster than expected during iterative testing.
11. **Timezone trap on submission.** Deadline is Aug 31, 5:00pm PDT. In IST that is **Sep 1, 5:30am** — i.e., late Monday night/early Tuesday morning your time, not "end of day Aug 31" as it might intuitively read. Plan your final submission push accordingly; don't lose the buffer to a timezone miscalculation.

---

## 13. Build Plan (Aug 19 → Aug 31)

| Days | Focus | Exit criteria |
|---|---|---|
| 1 | Spikes: Agent Platform access validated, OSM coverage checked for target zone, repo + billing alerts set up | A trivial ADK agent is confirmed running on Agent Runtime (or fallback decided) |
| 2–3 | Data layer: synthetic department datasets, OSM ingestion → mesh schema, Pub/Sub topics | Firestore populated with realistic `planned_works` records for 3–4 departments |
| 4–6 | Agent build: Department Agents, Coordinator conflict logic, ADK orchestration, deploy | Coordinator correctly flags a seeded conflict end-to-end |
| 7–8 | Governance: Identity scoping, Gateway + Model Armor on the citizen-input surface, Memory Bank wiring, Observability traces | Cross-department read denial demoable; prompt-injection attempt demoable; reasoning trace visible |
| 9–10 | Frontend: deck.gl wireframe mesh, live SSE updates, Citizen Notice Agent artifact generation | Mesh updates live on screen when a conflict resolves; PDF/ICS downloadable |
| 11 | Integration testing, failure-mode/loop guards, architecture diagram, README | End-to-end run works twice in a row without manual intervention |
| 12 | Record demo video, write text description, finalize repo license, submit with real buffer before the IST-adjusted deadline | Submission complete, confirmed received |

---

## 14. Submission Checklist (mapped to official requirements)

- [ ] Category selected: Fortified Enterprise Fleet
- [ ] Hosted project URL (Cloud Run frontend — encouraged, scores higher on Technical Implementation)
- [ ] Text description: features/functionality, technologies used, data sources, findings/learnings
- [ ] Public repo URL with MIT/Apache license visible + README with spin-up instructions
- [ ] Architecture diagram (use §5 as the base, clean it up visually)
- [ ] ~4-minute demo video: problem → value prop → live demo → visible proof of GCP backend (Cloud Run dashboard / Vertex AI logs / Agent Runtime console)
- [ ] (Bonus) Public blog/video post about the build, with required hackathon language and hashtag
- [ ] (Bonus) Veo/Gemma/Lyria integration — Veo b-roll clip is the cheapest path

---

## 15. Demo Video Outline (~4 min)

1. **0:00–0:30** — Problem: the "dig once" failure, stated plainly, maybe with the Veo b-roll as a cold open
2. **0:30–1:00** — Who it's for: municipal coordination offices, framed concretely
3. **1:00–2:30** — Live demo: seeded conflict appears on the wireframe mesh, Coordinator reasoning trace shown, cross-department Identity denial shown, Model Armor blocking a poisoned citizen input shown, resolution renders live, PDF/ICS notice generated
4. **2:30–3:30** — Architecture walkthrough over the diagram: Agent Platform pillars called out by name
5. **3:30–4:00** — Why it matters + close

---

## 16. Open Decisions

- Confirm which city/ward to target (drives OSM data quality — check coverage before locking this in)
- Confirm final product name (Diya is a placeholder)
- Decide fallback trigger point for Agent Platform access (recommend: end of Day 1)

