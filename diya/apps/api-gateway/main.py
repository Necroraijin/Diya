"""
DIYA API Gateway

The single seam between the agent/GIS layer and the frontend (PRD §5): agents
never talk to the browser directly. Everything is persisted through the
repository and pushed to connected clients over SSE.

State lives in diya_core's repository (in-memory by default, Firestore when
DIYA_STORE=firestore) rather than in module-level lists, so a restart or a
second replica no longer sees a different world.
"""

from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import Any, Optional

import httpx
from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

import gateway_policy
import governance
import observability
import registry
from gateway_policy import CircuitOpen
from observability import tracer
from diya_core.conflict import DetectionConfig
from diya_core.events import event_bus
from diya_core.models import (
    AgentActivity,
    Conflict,
    Notice,
    ProposedWindow,
    utcnow_iso,
)
from diya_core.pubsub import TOPIC_DEPARTMENT_FEED, get_publisher
from diya_core.repository import get_repository

MESH_SERVICE_URL = os.environ.get("MESH_SERVICE_URL", "http://localhost:8001")
AGENT_SERVICE_URL = os.environ.get("AGENT_SERVICE_URL", "http://localhost:8002")
NOTICE_SERVICE_URL = os.environ.get("NOTICE_SERVICE_URL", "http://localhost:8003")

ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
]

repository = get_repository()
publisher = get_publisher()
http_client: Optional[httpx.AsyncClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(timeout=30.0)
    await repository.init()
    await _record(
        "Coordinator Agent", "coordinator", "Startup Detection Scan",
        f"Loaded {len(await repository.list_works())} planned works; "
        f"{len(await repository.list_conflicts())} conflicts detected.",
    )
    yield
    await http_client.aclose()


app = FastAPI(
    title="DIYA API Gateway",
    description="Multi-Agent Infrastructure Conflict Resolution System",
    version="2.0.0",
    lifespan=lifespan,
)

# allow_credentials with a wildcard origin is rejected by browsers, so origins
# are enumerated explicitly and overridable per environment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ── Agent Gateway middleware ─────────────────────────────────────

# The surface agents and untrusted callers reach. Read-only browsing by the
# dashboard is not rate limited — throttling a coordinator's page refresh buys
# nothing, while the agent and citizen surfaces are where a runaway loop or an
# abusive client actually shows up.
_POLICED_PREFIXES = (
    "/api/complaints",
    "/api/conflicts/detect",
    "/api/ingest",
    "/api/governance",
)


def _caller_of(request: Request) -> str:
    """
    Who to bill this request to.

    An explicit agent identity wins, so one looping agent is throttled without
    affecting the rest of the fleet. Otherwise fall back to the peer address.
    """
    identity = request.headers.get("x-agent-identity") or request.query_params.get("agent_id")
    if identity:
        return identity.strip().lower()
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def agent_gateway(request: Request, call_next):
    """Trace every request; rate limit the agent-facing and citizen surfaces."""
    path = request.url.path

    if request.method != "OPTIONS" and path.startswith(_POLICED_PREFIXES):
        caller = _caller_of(request)
        allowed, retry_after = await gateway_policy.rate_limiter.check(caller)
        if not allowed:
            await _record(
                "Agent Gateway", "governance", "Rate Limit",
                f"THROTTLED {caller} on {path}: over "
                f"{gateway_policy.RATE_LIMIT_PER_MIN}/min. Retry in {retry_after}s.",
                status="blocked",
            )
            return Response(
                content=json.dumps({
                    "detail": (
                        f"Rate limit of {gateway_policy.RATE_LIMIT_PER_MIN}/min exceeded "
                        f"for {caller}."
                    ),
                    "retryAfter": retry_after,
                }),
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(max(1, int(retry_after)))},
            )

    with tracer.span(f"{request.method} {path}", kind="server") as span:
        span.set(method=request.method, path=path, caller=_caller_of(request))
        response = await call_next(request)
        span.set(status=response.status_code)
        if response.status_code >= 500:
            span.status = "error"
        # Hand the trace id back so a caller can pull the span tree for the
        # exact request it just made.
        response.headers["X-Trace-Id"] = span.traceId
        return response


# ── Request models ───────────────────────────────────────────────

class ResolveRequest(BaseModel):
    resolution_type: str = "consolidated"
    notes: Optional[str] = None
    generate_notice: bool = True


class CitizenComplaint(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    location: Optional[str] = None
    contact: Optional[str] = None


class DetectRequest(BaseModel):
    config: Optional[DetectionConfig] = None


# ── Helpers ──────────────────────────────────────────────────────

async def _record(
    agent_name: str, agent_type: str, action: str, detail: str,
    status: str = "success", trace_id: Optional[str] = None,
    duration: Optional[int] = None, publish: bool = True,
) -> AgentActivity:
    """Persist an agent activity and push it to connected clients."""
    activity = AgentActivity(
        id=f"act-{utcnow_iso()}-{abs(hash(detail)) % 10_000:04d}",
        agentName=agent_name,
        agentType=agent_type,  # type: ignore[arg-type]
        action=action,
        detail=detail,
        status=status,  # type: ignore[arg-type]
        traceId=trace_id,
        duration=duration,
    )
    await repository.add_activity(activity)
    if publish:
        await event_bus.publish("agent.activity", {"activity": activity.model_dump()})
    return activity


_SERVICE_NAMES = {
    MESH_SERVICE_URL: "mesh-service",
    AGENT_SERVICE_URL: "agent-service",
    NOTICE_SERVICE_URL: "notice-service",
}


async def _call_upstream(
    method: str, base: str, path: str, raw: bool = False, **kwargs
) -> Any:
    """
    Every upstream call goes through the breaker and the timeout.

    A 4xx from a healthy service is a *caller* error, not an upstream failure —
    counting it toward the breaker would let one bad request id trip the circuit
    for everyone. Only transport errors and 5xx count against it.
    """
    assert http_client is not None
    service = _SERVICE_NAMES.get(base, base)
    breaker = gateway_policy.breaker_for(service)

    if not breaker.allows():
        raise HTTPException(
            status_code=503,
            detail=str(CircuitOpen(breaker)),
            headers={"Retry-After": str(int(breaker.retry_after()) or 1)},
        )

    with tracer.span(f"upstream.{service}", kind="client") as span:
        span.set(method=method, path=path, breaker=breaker.state)
        try:
            response = await http_client.request(
                method, f"{base}{path}", timeout=gateway_policy.TIMEOUT_SECONDS, **kwargs
            )
        except httpx.HTTPError as exc:
            breaker.record_failure()
            raise HTTPException(
                status_code=503, detail=f"Upstream {base}{path} unreachable: {exc}"
            ) from exc

        span.set(status=response.status_code)
        if response.status_code >= 500:
            breaker.record_failure()
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Upstream {base}{path}: {response.text[:200]}",
            )

        breaker.record_success()
        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Upstream {base}{path}: {response.text[:200]}",
            )
        return response if raw else response.json()


async def _service_get(base: str, path: str, **params) -> Any:
    return await _call_upstream("GET", base, path, params=params or None)


async def _service_post(base: str, path: str, payload: dict) -> Any:
    return await _call_upstream("POST", base, path, json=payload)


# ── Health ───────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"service": "DIYA API Gateway", "status": "operational", "version": "2.0.0"}


@app.get("/health")
async def health():
    """Reports real upstream health rather than asserting everything is up."""
    services: dict[str, str] = {"api-gateway": "up"}

    async def probe(name: str, base: str) -> None:
        try:
            assert http_client is not None
            response = await http_client.get(f"{base}/health", timeout=3.0)
            services[name] = "up" if response.status_code == 200 else "degraded"
        except httpx.HTTPError:
            services[name] = "down"

    await asyncio.gather(
        probe("mesh-service", MESH_SERVICE_URL),
        probe("agent-service", AGENT_SERVICE_URL),
        probe("notice-service", NOTICE_SERVICE_URL),
    )

    return {
        "status": "healthy" if all(v == "up" for v in services.values()) else "degraded",
        "timestamp": utcnow_iso(),
        "services": services,
        "store": type(repository).__name__,
        "pubsub": "enabled" if publisher.enabled else "local",
        "sse_subscribers": event_bus.subscriber_count,
    }


# ── Departments ──────────────────────────────────────────────────

@app.get("/api/departments")
async def list_departments():
    departments = await repository.list_departments()
    return {
        "departments": [d.model_dump() for d in departments],
        "count": len(departments),
    }


@app.get("/api/departments/{dept_id}")
async def get_department(dept_id: str):
    department = next(
        (d for d in await repository.list_departments() if d.id == dept_id), None
    )
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    works = await repository.list_works(dept_id=dept_id)
    return {**department.model_dump(), "works": [w.model_dump() for w in works]}


# ── Planned works ────────────────────────────────────────────────

@app.get("/api/planned-works")
async def list_planned_works(
    dept_id: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    works = await repository.list_works(dept_id=dept_id, city=city, status=status)
    return {
        "planned_works": [w.model_dump() for w in works],
        "count": len(works),
    }


@app.get("/api/planned-works/{work_id}")
async def get_planned_work(work_id: str):
    work = await repository.get_work(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Planned work not found")
    return work.model_dump()


# ── Conflicts ────────────────────────────────────────────────────

@app.get("/api/conflicts")
async def list_conflicts(
    status: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
):
    conflicts = await repository.list_conflicts(status=status, city=city)
    works = {w.id: w for w in await repository.list_works()}
    return {
        "conflicts": [
            {
                **c.model_dump(),
                "works": [works[i].model_dump() for i in c.workIds if i in works],
            }
            for c in conflicts
        ],
        "count": len(conflicts),
    }


@app.get("/api/conflicts/{conflict_id}")
async def get_conflict(conflict_id: str):
    conflict = await repository.get_conflict(conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    works = [await repository.get_work(i) for i in conflict.workIds]
    return {
        **conflict.model_dump(),
        "works": [w.model_dump() for w in works if w],
    }


@app.post("/api/conflicts/detect")
async def run_detection(request: DetectRequest = Body(default=DetectRequest())):
    """Re-run conflict detection across every stored work."""
    conflicts = await repository.run_detection(request.config)
    await _record(
        "Coordinator Agent", "coordinator", "Conflict Detection",
        f"Scan complete: {len(conflicts)} conflict(s) across "
        f"{len(await repository.list_works())} planned works.",
    )
    await event_bus.publish("conflict.detected", {"count": len(conflicts)})
    return {
        "conflicts": [c.model_dump() for c in conflicts],
        "count": len(conflicts),
    }


@app.post("/api/conflicts/{conflict_id}/resolve")
async def resolve_conflict(conflict_id: str, body: ResolveRequest):
    """
    Mark a conflict resolved and generate its citizen notice.

    This is the end of the "real action" chain (PRD red flag #6): resolution
    produces a downloadable PDF and ICS, not just a status change.
    """
    conflict = await repository.get_conflict(conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    if conflict.status == "resolved":
        raise HTTPException(status_code=409, detail="Conflict is already resolved")

    conflict.status = "dismissed" if body.resolution_type == "dismiss" else "resolved"
    conflict.resolvedAt = utcnow_iso()
    await repository.upsert_conflict(conflict)

    await _record(
        "Coordinator Agent", "coordinator", "Conflict Resolution",
        f"{conflict_id} marked {conflict.status} "
        f"({body.resolution_type}). {body.notes or ''}".strip(),
        trace_id=conflict.traceId,
    )
    await event_bus.publish(
        "conflict.resolved",
        {"conflictId": conflict_id, "status": conflict.status},
    )

    notice: Optional[Notice] = None
    notice_error: Optional[str] = None

    if conflict.status == "resolved" and body.generate_notice:
        try:
            notice = await _generate_notice(conflict)
        except Exception as exc:  # noqa: BLE001
            # A notice-service failure must not roll back or 500 a resolution
            # the coordinator has already committed; surface it instead.
            notice_error = (
                str(exc.detail) if isinstance(exc, HTTPException) else f"{type(exc).__name__}: {exc}"
            )
            await _record(
                "Citizen Notice Agent", "notice", "Notice Generation",
                f"Failed for {conflict_id}: {notice_error}", status="error",
            )

    return {
        "conflict_id": conflict_id,
        "status": conflict.status,
        "resolution_type": body.resolution_type,
        "resolved_at": conflict.resolvedAt,
        "notice": notice.model_dump() if notice else None,
        "notice_error": notice_error,
        "message": (
            f"Conflict {conflict.status}."
            + (" Citizen notice generated." if notice else "")
        ),
    }


async def _generate_notice(conflict: Conflict) -> Notice:
    """Call the notice service and persist the resulting artifact record."""
    fetched = await asyncio.gather(
        *(repository.get_work(i) for i in conflict.workIds)
    )
    works = [w for w in fetched if w]
    departments = sorted({w.deptName for w in works})
    area = conflict.locationSummary or "Affected area"

    payload = {
        "conflict_id": conflict.id,
        "title": f"Consolidated Infrastructure Works — {area}",
        "description": (
            f"{len(works)} separate excavations of this stretch, planned "
            f"independently by {len(departments)} departments "
            f"({', '.join(departments)}), have been merged into a single "
            f"coordinated closure."
        ),
        "affected_area": area,
        "closure_start": conflict.proposedWindow.start,
        "closure_end": conflict.proposedWindow.end,
        "departments": departments,
        "phases": [p.model_dump() for p in conflict.proposedWindow.phases],
        "city": conflict.city,
        "savings": conflict.savings,
    }

    result = await _service_post(NOTICE_SERVICE_URL, "/notices/generate", payload)

    notice = Notice(
        id=result["notice_id"],
        conflictId=conflict.id,
        title=payload["title"],
        description=payload["description"],
        affectedArea=area,
        closureWindow=ProposedWindow(
            start=conflict.proposedWindow.start,
            end=conflict.proposedWindow.end,
            phases=conflict.proposedWindow.phases,
        ),
        departments=departments,
        pdfUrl=f"/api/notices/{result['notice_id']}/pdf",
        icsUrl=f"/api/notices/{result['notice_id']}/ics",
        generatedAt=result["generated_at"],
        status="published",
    )
    await repository.upsert_notice(notice)

    await _record(
        "Citizen Notice Agent", "notice", "Notice Generation",
        f"Generated PDF and ICS for {conflict.id} covering "
        f"{payload['closure_start']} to {payload['closure_end']}.",
    )
    await event_bus.publish("notice.generated", {"notice": notice.model_dump()})
    return notice


# ── Mesh ─────────────────────────────────────────────────────────

@app.get("/api/mesh/{city}")
async def get_mesh(city: str, refresh: bool = Query(False)):
    """Building and road geometry, proxied from the mesh service."""
    return await _service_get(MESH_SERVICE_URL, f"/mesh/{city}", refresh=refresh)


@app.get("/api/mesh/{city}/conflict-zones")
async def get_conflict_zones(city: str):
    """GeoJSON overlay of every area where geofences collide in this city."""
    works = await repository.list_works(city=city)
    if len(works) < 2:
        return {"type": "FeatureCollection", "features": []}
    return await _service_post(
        MESH_SERVICE_URL,
        "/spatial/conflict-zones",
        {"works": [w.model_dump() for w in works]},
    )


@app.get("/api/cities")
async def list_cities():
    return await _service_get(MESH_SERVICE_URL, "/cities")


# ── Notices ──────────────────────────────────────────────────────

@app.get("/api/notices")
async def list_notices():
    notices = await repository.list_notices()
    return {"notices": [n.model_dump() for n in notices], "count": len(notices)}


@app.get("/api/notices/{notice_id}")
async def get_notice(notice_id: str):
    notice = await repository.get_notice(notice_id)
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    return notice.model_dump()


@app.get("/api/notices/{notice_id}/{artifact}")
async def download_artifact(notice_id: str, artifact: str):
    """Stream a generated PDF or ICS through the gateway to the browser."""
    if artifact not in ("pdf", "ics"):
        raise HTTPException(status_code=404, detail="Expected 'pdf' or 'ics'")

    # Through the breaker like every other upstream call — an artifact download
    # against a dead notice service must fail fast too, not hang per request.
    upstream = await _call_upstream(
        "GET", NOTICE_SERVICE_URL, f"/notices/{notice_id}/{artifact}", raw=True
    )

    media = "application/pdf" if artifact == "pdf" else "text/calendar"
    disposition = "inline" if artifact == "pdf" else "attachment"
    return Response(
        content=upstream.content,
        media_type=media,
        headers={
            "Content-Disposition": f'{disposition}; filename="{notice_id}.{artifact}"'
        },
    )


# ── Agents ───────────────────────────────────────────────────────

@app.get("/api/agents/activity")
async def agent_activity(
    agent_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    activities = await repository.list_activities(agent_type=agent_type, limit=limit)
    return {
        "activities": [a.model_dump() for a in activities],
        "count": len(activities),
    }


@app.get("/api/agents/status")
async def agent_status():
    return await _service_get(AGENT_SERVICE_URL, "/agents/status")


@app.get("/api/agents/traces/{trace_id}")
async def get_trace(trace_id: str):
    """
    The reasoning trace behind a detection.

    Every step is the computation the detector actually performed, so "why did
    it flag these two projects" has a real answer (PRD §10).
    """
    conflict_id = trace_id.removeprefix("trace-")
    conflict = await repository.get_conflict(conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail=f"No trace for '{trace_id}'")

    return {
        "trace_id": trace_id,
        "agent": "Coordinator Agent",
        "conflict_id": conflict.id,
        "steps": [s.model_dump() for s in conflict.reasoningSteps],
        "total_duration": sum(s.durationMs for s in conflict.reasoningSteps),
        "outcome": conflict.reasoningTrace,
        "severity": conflict.severity,
        "detected_at": conflict.detectedAt,
    }


# ── Citizen complaints (Model Armor surface) ─────────────────────

@app.post("/api/complaints")
async def submit_complaint(complaint: CitizenComplaint):
    """
    The one untrusted external input in the system (PRD §10).

    Model Armor screens it before any agent sees it.
    """
    verdict = governance.scan(complaint.text)

    if verdict.status == "blocked":
        await _record(
            "Model Armor", "governance", "Input Screening",
            f"BLOCKED citizen complaint: {verdict.detail}",
            status="blocked",
        )
        await event_bus.publish(
            "armor.blocked",
            {"severity": verdict.severity, "threats": verdict.threats},
        )
        return {
            "status": "blocked",
            "reason": "Model Armor: malicious input detected",
            "severity": verdict.severity,
            "threats": verdict.threats,
            "detail": verdict.detail,
            "sanitized_preview": verdict.sanitized,
        }

    complaint_id = f"cmp-{utcnow_iso()}"
    await _record(
        "Model Armor", "governance", "Input Screening",
        f"Citizen complaint {complaint_id} cleared for agent processing.",
    )
    return {
        "status": "accepted",
        "message": "Complaint received and forwarded for processing",
        "complaint_id": complaint_id,
    }


# ── Governance ───────────────────────────────────────────────────

@app.get("/api/governance/identity/verify")
async def verify_identity(
    agent_id: str = Query(...),
    resource: str = Query(...),
    action: str = Query("read"),
):
    decision = governance.check_identity(agent_id, resource, action)
    await _record(
        "Agent Identity", "governance", "Scope Check",
        f"{decision.result}: {agent_id} -> {action} {resource}. {decision.reason}",
        status="success" if decision.result == "GRANTED" else "blocked",
    )
    return decision.__dict__


@app.post("/api/governance/armor/scan")
async def armor_scan(complaint: CitizenComplaint):
    verdict = governance.scan(complaint.text)
    return {
        "status": verdict.status,
        "severity": verdict.severity,
        "threats": verdict.threats,
        "threat_count": len(verdict.threats),
        "detail": verdict.detail,
        "sanitized_output": verdict.sanitized,
    }


@app.get("/api/governance/stats")
async def governance_stats():
    """Governance counters derived from the real activity log."""
    activities = await repository.list_activities(agent_type="governance", limit=500)
    identity = [a for a in activities if a.action == "Scope Check"]
    armor = [a for a in activities if a.action == "Input Screening"]
    throttled = [a for a in activities if a.action == "Rate Limit"]

    return {
        "identity_checks": {
            "total": len(identity),
            "granted": sum(1 for a in identity if a.status == "success"),
            "denied": sum(1 for a in identity if a.status == "blocked"),
        },
        "armor_scans": {
            "total": len(armor),
            "blocked": sum(1 for a in armor if a.status == "blocked"),
            "passed": sum(1 for a in armor if a.status == "success"),
        },
        "rate_limit": {
            "throttled": len(throttled),
            "recent": [a.detail for a in throttled[:5]],
        },
        # Phase 2 reported these as configuration. They are now enforced, and
        # this block is the live state of the enforcement — including how many
        # callers are being tracked and whether any breaker has tripped.
        "runtime": {
            "max_turns": int(os.environ.get("AGENT_MAX_TURNS", 10)),
            **gateway_policy.policy_snapshot(),
        },
        "observability": tracer.stats(),
        "armor_patterns": len(governance.ARMOR_PATTERNS),
        "cross_department_scopes": sorted(governance.CROSS_DEPARTMENT_SCOPES),
        "functional_scopes": {
            scope: {c: sorted(a) for c, a in grants.items()}
            for scope, grants in governance.FUNCTIONAL_SCOPES.items()
        },
    }


# ── Agent Observability (PRD §10) ────────────────────────────────

@app.get("/api/observability/traces")
async def list_traces(limit: int = Query(20, ge=1, le=200)):
    """Recent request traces, newest first."""
    return {
        "traces": tracer.recent(limit),
        "stats": tracer.stats(),
    }


@app.get("/api/observability/traces/{trace_id}")
async def get_trace(trace_id: str):
    """
    The full span tree for one request.

    Every response carries its own id in `X-Trace-Id`, so "why did that call
    take four seconds" is answerable for the exact request that did it.
    """
    trace = tracer.trace(trace_id)
    if not trace:
        raise HTTPException(
            status_code=404,
            detail=f"No trace {trace_id}. The buffer holds the last "
                   f"{tracer.stats()['capacity']} traces.",
        )
    return trace


# ── Agent Registry (PRD §9) ──────────────────────────────────────

@app.get("/api/registry")
async def agent_registry():
    """
    The registered fleet, reconciled against the agents actually running.

    A register nobody checks drifts and then misleads, so this reports the
    difference rather than just listing what it was told.
    """
    try:
        topology = await _service_get(AGENT_SERVICE_URL, "/agents/topology")
    except HTTPException:
        topology = None

    return {
        "agents": registry.register(),
        "count": len(registry.register()),
        "version": registry.REGISTRY_VERSION,
        "deployment": registry.DEPLOYMENT_TARGET,
        "reconciliation": registry.reconcile(topology),
    }


# ── Ingestion (Pub/Sub) ──────────────────────────────────────────

@app.post("/api/ingest/{dept_id}")
async def ingest_department_feed(dept_id: str):
    """
    Publish a department's feed onto Pub/Sub for asynchronous normalisation.

    Falls back to a local publisher when GCP is not configured, so the ingestion
    path is exercisable offline.
    """
    works = await repository.list_works(dept_id=dept_id)
    if not works:
        raise HTTPException(status_code=404, detail=f"No works for '{dept_id}'")

    message_id = publisher.publish_department_feed(
        dept_id, [w.model_dump() for w in works]
    )
    await _record(
        f"{dept_id} Agent", "department", "Feed Ingestion",
        f"Published {len(works)} record(s) to {TOPIC_DEPARTMENT_FEED}.",
    )
    return {
        "dept_id": dept_id,
        "records": len(works),
        "topic": TOPIC_DEPARTMENT_FEED,
        "message_id": message_id,
        "mode": "pubsub" if publisher.enabled else "local",
    }


# ── SSE ──────────────────────────────────────────────────────────

@app.get("/api/events")
async def event_stream(request: Request):
    """
    Real-time domain events.

    Emits actual conflict/notice/governance events as they happen, with a
    periodic heartbeat only to keep intermediaries from closing an idle stream.
    """
    async def generate():
        async with event_bus.subscribe() as queue:
            snapshot = {
                "type": "connected",
                "timestamp": utcnow_iso(),
                "active_conflicts": len(await repository.list_conflicts(status="detected")),
                "notices": len(await repository.list_notices()),
            }
            yield f"data: {json.dumps(snapshot)}\n\n"

            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    event = {"type": "heartbeat", "timestamp": utcnow_iso()}
                yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # keeps nginx/Cloud Run from buffering SSE
        },
    )


# ── Dashboard ────────────────────────────────────────────────────

@app.get("/api/dashboard/metrics")
async def dashboard_metrics():
    conflicts = await repository.list_conflicts()
    works = await repository.list_works()
    departments = await repository.list_departments()
    notices = await repository.list_notices()

    resolved = [c for c in conflicts if c.status == "resolved"]

    return {
        "totalConflicts": len(conflicts),
        "resolvedConflicts": len(resolved),
        "activeWorks": len(works),
        "departments": len(departments),
        # Only realised savings count — an unresolved conflict has saved nothing.
        "estimatedSavings": sum(c.savings for c in resolved),
        "potentialSavings": sum(c.savings for c in conflicts),
        "citizenNotices": len(notices),
        "departmentBreakdown": [
            {
                "name": d.shortName,
                "works": sum(1 for w in works if w.deptId == d.id),
                "conflicts": sum(
                    1 for c in conflicts
                    if any(w.deptId == d.id for w in works if w.id in c.workIds)
                ),
            }
            for d in departments
        ],
        "severityBreakdown": {
            level: sum(1 for c in conflicts if c.severity == level)
            for level in ("critical", "high", "medium", "low")
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
