# DIYA — Submission Text

All Things Agentic Hackathon 2026 · **Fortified Enterprise Fleet** track.

Copy the section you need. The short version is the one most forms want.

---

## Short (≈100 words)

Four municipal departments plan work on the same 200 metres of SV Road. None
knows about the other three, so the road is opened, paved, and opened again.
DIYA is an agent fleet that reads every department's plan, finds the spatial and
temporal collisions, and merges them into one dig sequenced by excavation depth
— sewer, water, fibre, then resurfacing, because surface work must be last.

Four Department Agents run in parallel under scoped identities; a Coordinator
holds the only cross-department read scope; a Citizen Notice Agent emits a real
PDF and calendar file. Every tool call is identity-checked at an Agent Gateway.
The agents hold no store credentials.

---

## Medium (≈250 words)

**The problem.** Indian cities re-dig the same roads because departments plan in
silos. The water utility, the sewage board, telecom and the roads department all
target the same stretch within months of each other, and each one restores the
surface that the next one breaks. The waste is mundane, enormous, and entirely
one of coordination.

**What DIYA does.** A fleet of Google ADK agents ingests each department's
planned works, detects conflicts by geofence penetration and calendar overlap,
and proposes one consolidated closure window ordered by excavation depth. For
the demo conflict — four departments, one OSM way, 273 metres of geofence
penetration — it collapses 196 closure-days across four separate closures into
144 in one, a 27% reduction and ₹1.44 crore of avoided mobilisation and
restoration. Resolution generates a real citizen notice: a downloadable PDF and
an ICS calendar file.

**Why it holds up.** The arithmetic lives in a shared Python package that both
execution paths call as a tool, so the model narrates numbers it did not
compute. An agent inventing an overlap distance is the fastest way to lose
anyone who checks one.

**Governance** is enforced rather than declared. Agent Identity scopes are
checked on every tool call — the water agent reading the roads department is
refused, and the Coordinator is the single elevated identity. The Agent Gateway
applies a per-caller rate limit, timeouts, and a per-upstream circuit breaker to
real traffic. Model Armor screens the citizen input surface, redacting rather
than discarding so genuine complaints still get filed. A Memory Bank gives the
fleet cross-session recall. The Agent Registry reconciles the declared fleet
against the running one and reports drift.

---

## Long (≈500 words)

### The problem

Municipal departments in Indian cities plan infrastructure work independently.
The water utility schedules a main replacement; the sewage board schedules a
storm drain upgrade; telecom lays fibre; the roads department resurfaces. All
four target the same 200 metres of SV Road, Andheri West, within one season, and
each restores a surface the next one breaks. The cost is repeated excavation,
repeated restoration, repeated traffic diversion, and a public that watches the
same road be dug up three times a year.

This is not a data problem — every department's plan is already written down. It
is a coordination problem, which is what makes it a good fit for agents.

### The system

DIYA runs a fleet of Google ADK agents behind an API gateway:

- **Four Department Agents** run in parallel, one per department, each holding
  exactly two tools and one identity scoped to its own department. They read
  their feed and normalise their records; they cannot see each other's data.
- **A Coordinator Agent** holds the only cross-department read scope in the
  fleet. It detects conflicts, orders them by excavation depth, and proposes a
  consolidated window. A max-turn cap on its negotiation loop is enforced by the
  runner, not by instruction.
- **A Citizen Notice Agent** runs only on resolution and emits the artifacts —
  a PDF notice and an ICS calendar file.

Supporting services handle GIS (Overpass/OSM with Shapely geometry) and document
generation (ReportLab, icalendar).

### What makes the output trustworthy

The conflict arithmetic — geofence penetration in metres, date overlap,
depth-ordered sequencing, avoided cost — lives in a shared Python package that
the agents call as a tool. With a Gemini backend configured the ADK tree runs;
without one, the same tools execute in the same order deterministically. Both
paths report which ran, and both produce identical numbers, because neither
computes them. The model narrates; it does not calculate.

Ordering is derived from physics rather than preference: sewer inverts sit below
water mains, which sit below fibre ducts, and surface work must be last or it
gets re-opened. Each phase carries the rationale for its position.

### Governance

Built for the Fortified Enterprise Fleet track, so the controls are enforced
rather than advertised:

- **Agent Identity** — department and functional scopes checked on *every* tool
  call. The water agent reading `departments/dept-roads/**` is refused and
  logged.
- **Agent Gateway** — token-bucket rate limiting per caller identity, per-call
  timeouts, and a per-upstream circuit breaker. `/api/governance/stats` reports
  live enforcement state, not environment variables.
- **Model Armor** — anchored pattern screening on the citizen input surface,
  redacting rather than discarding so a real complaint containing one bad
  sentence still gets filed.
- **Memory Bank** — cross-session recall, so a re-run recognises a conflict it
  has already surfaced and does not re-flag one already signed off.
- **Observability** — a span tree per request with real timings and a trace id
  on every response.
- **Agent Registry** — the declared fleet reconciled against the running agent
  tree, reporting `in_sync`, `drift`, or `unknown`. "I could not check" is never
  reported as agreement.

### Honesty about scope

All department data is synthetic, using real OSM road names and realistic
municipal naming but no actual government record or citizen. The stack runs
entirely offline; deploying to Cloud Run, Vertex Agent Engine and managed Cloud
Trace needs a GCP project rather than more code. The dashboard shows whether it
is reading the live backend or seeded fixtures, and says so in the top bar —
because a dashboard that quietly serves stale numbers when its backend dies is
worse than one that crashes.

---

## Fact sheet

| | |
|---|---|
| Track | Fortified Enterprise Fleet |
| Agent framework | Google ADK 2.7.1 (`LlmAgent`, `ParallelAgent`, `SequentialAgent`) |
| Model | Gemini (`gemini-flash-latest`); deterministic fallback over the same tools |
| Agents | 4 department + 1 coordinator + 1 notice = 6, in one `SequentialAgent` |
| Services | Next.js 14 web · FastAPI gateway · agent · mesh · notice |
| Governance | Identity · Gateway · Model Armor · Memory Bank · Observability · Registry |
| Demo conflict | 4 departments, 1 OSM way, 273 m geofence penetration, 6/6 pairs overlapping |
| Outcome | 196 closure-days → 144 (27% reduction); ₹1.44 Cr; 4 closures → 1 |
| Artifacts | PDF notice (4.2 KB) + ICS calendar (2.5 KB), downloadable |
| Data | Synthetic; real OSM road names, no real records or citizens |
| License | MIT |

---

## Pre-submission checklist

- [x] Repo cleanup — no TODOs, placeholders, dead endpoints, or stray logging
- [x] LICENSE file present (MIT), matching the README
- [x] No credentials or `.env` tracked in git
- [x] `tsc --noEmit` and `next build` green
- [x] Full stack boots clean and `/health` reports `healthy`
- [ ] Demo video recorded (~4 min) — script in `docs/demo.md`
- [ ] Submitted before the deadline (Sep 1, 5:30am IST)
