"""
DIYA Agent Service

The ADK agent fleet (PRD §6) and its orchestration (PRD §6.4).

Execution has two paths over one tool set. With a Gemini backend configured the
real ADK tree runs; without one the same tools execute in the same order
deterministically. `GET /health` and every run response say which path was
taken, because a demo that silently falls back to a scripted sequence while
implying an LLM ran would be the dishonest kind of fallback.

The arithmetic is deterministic on both paths by design — see `agents.py`.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import agents as fleet
import orchestrator
import tools
from memory import memory_bank

from diya_core.models import utcnow_iso
from diya_core.seed import load_seed

app = FastAPI(
    title="DIYA Agent Service",
    description="ADK agent fleet: department ingestion, coordination, citizen notices",
    version="3.0.0",
)

ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost:8000")
MAX_TURNS = int(os.environ.get("AGENT_MAX_TURNS", 10))

DEFAULT_PROMPT = (
    "Ingest every department feed, detect cross-department conflicts, and "
    "propose a consolidated window for each new one."
)


def _departments() -> list[dict]:
    return [d.model_dump() for d in load_seed().departments]


def _execution_mode() -> tuple[str, str]:
    """The path a run would take right now, and why."""
    has_adk, adk_reason = fleet.adk_available()
    if not has_adk:
        return "deterministic", adk_reason
    has_llm, llm_reason = fleet.vertex_configured()
    if not has_llm:
        return "deterministic", llm_reason
    return "adk", ""


# ── Models ───────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    dept_id: str
    feed_source: Optional[str] = None


class ResolutionRequest(BaseModel):
    conflict_id: str
    strategy: str = "consolidated"
    notes: str = ""


class RunRequest(BaseModel):
    prompt: str = DEFAULT_PROMPT
    # Off by default: the Coordinator proposes, a human signs off, and only
    # then does the Notice Agent issue anything.
    auto_resolve: bool = False
    force_mode: Optional[str] = None  # "adk" | "deterministic"


# ── Routes ───────────────────────────────────────────────────────

@app.get("/")
async def root():
    mode, _ = _execution_mode()
    return {
        "service": "DIYA Agent Service",
        "status": "operational",
        "version": "3.0.0",
        "execution_mode": mode,
    }


@app.get("/health")
async def health():
    mode, reason = _execution_mode()
    has_adk, _ = fleet.adk_available()
    return {
        "status": "healthy",
        "adk_installed": has_adk,
        "execution_mode": mode,
        "execution_mode_reason": reason or "LLM backend configured.",
        "model": fleet.MODEL,
        "max_turns": MAX_TURNS,
        "memory_backend": memory_bank.backend,
        "gateway": GATEWAY_URL,
        "gateway_error": await tools.gateway_reachable(),
    }


@app.get("/agents/status")
async def agents_status():
    """
    The agent fleet, derived from the seeded departments.

    One Department Agent per department, each with its own Agent Identity, plus
    the Coordinator and the Citizen Notice Agent (PRD §6).
    """
    seed = load_seed()
    mode, _ = _execution_mode()

    agents = [
        {
            "name": f"{d.shortName} Department Agent",
            "type": "department",
            "identityId": d.agentIdentityId,
            "scope": f"departments/{d.id}/**",
            "crossDepartmentRead": False,
            "status": "online",
            "recordsInScope": d.activeWorks,
            "tools": ["read_department_feed", "write_normalized_record"],
        }
        for d in seed.departments
    ]

    agents.append({
        "name": "Coordinator Agent",
        "type": "coordinator",
        "identityId": tools.COORDINATOR_IDENTITY,
        "scope": "departments/**",
        # The single elevated identity in the system — PRD §6.2.
        "crossDepartmentRead": True,
        "status": "online",
        "recordsInScope": len(seed.works),
        "maxTurns": MAX_TURNS,
        "tools": [
            "read_all_planned_works", "detect_conflicts",
            "propose_consolidated_window", "recall_conflict", "remember_conflict",
        ],
    })
    agents.append({
        "name": "Citizen Notice Agent",
        "type": "notice",
        "identityId": tools.NOTICE_IDENTITY,
        "scope": "conflicts/**:read, notices/**:write",
        "crossDepartmentRead": False,
        "status": "online",
        "tools": ["resolve_and_generate_notice"],
    })

    return {
        "agents": agents,
        "count": len(agents),
        "timestamp": utcnow_iso(),
        "execution_mode": mode,
    }


@app.get("/agents/topology")
async def agents_topology():
    """
    The ADK orchestration tree: ParallelAgent -> Coordinator -> Notice.

    Built from the real agent objects, so the architecture diagram cannot drift
    away from the code it claims to describe.
    """
    root = fleet.build_fleet(_departments())
    if root is None:
        raise HTTPException(
            status_code=503,
            detail="google-adk is not installed; the agent tree cannot be built.",
        )
    return {"root": fleet.describe_fleet(root), "pattern": "ParallelAgent -> SequentialAgent"}


@app.post("/agents/run")
async def run_pipeline(request: RunRequest):
    """Run the full pipeline: ingestion -> coordination -> (optional) notice."""
    mode, reason = _execution_mode()
    if request.force_mode:
        mode = request.force_mode

    if mode == "adk":
        result = await orchestrator.run_adk(_departments(), request.prompt)
        # A failed model call must not swallow the run: fall through to the
        # deterministic path and say that is what happened.
        if result.error:
            fallback = await orchestrator.run_deterministic(
                _departments(), auto_resolve=request.auto_resolve
            )
            fallback.error = f"ADK path failed, ran deterministically instead: {result.error}"
            return fallback.dump()
        return result.dump()

    result = await orchestrator.run_deterministic(
        _departments(), auto_resolve=request.auto_resolve
    )
    payload = result.dump()
    payload["mode_reason"] = reason
    return payload


@app.post("/agents/department/ingest")
async def ingest_department_feed(request: IngestRequest):
    """Run one Department Agent: read its own feed, publish the normalised batch."""
    seed = load_seed()
    dept = next((d for d in seed.departments if d.id == request.dept_id), None)
    if not dept:
        raise HTTPException(status_code=404, detail=f"Unknown department '{request.dept_id}'")

    try:
        feed = await tools.read_department_feed(dept.id, dept.agentIdentityId)
        published = await tools.write_normalized_record(dept.id, dept.agentIdentityId)
    except tools.ScopeDenied as denied:
        raise HTTPException(status_code=403, detail=denied.reason) from denied
    except tools.GatewayError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "dept_id": dept.id,
        "identity": dept.agentIdentityId,
        "records_read": feed["count"],
        "published": published,
    }


@app.post("/agents/coordinator/detect")
async def coordinator_detect():
    """Run the Coordinator's detection leg on its own."""
    try:
        detected = await tools.detect_conflicts()
    except tools.ScopeDenied as denied:
        raise HTTPException(status_code=403, detail=denied.reason) from denied
    except tools.GatewayError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    conflicts = detected.get("conflicts", [])
    remembered = [
        memory_bank.remember(
            c["id"], outcome=c["status"], work_ids=c.get("workIds", []),
            detail=c.get("description", ""),
        )
        for c in conflicts
    ]
    return {
        "conflicts": conflicts,
        "count": len(conflicts),
        "memory": remembered,
    }


@app.post("/agents/coordinator/resolve")
async def coordinator_resolve(request: ResolutionRequest):
    """
    Sign off a conflict and hand it to the Citizen Notice Agent.

    This is the conditional transfer in the orchestration pattern (PRD §6.4):
    the Notice Agent runs only once a conflict resolves to "consolidated".
    """
    try:
        outcome = await tools.resolve_and_generate_notice(
            request.conflict_id, request.strategy, request.notes
        )
    except tools.ScopeDenied as denied:
        raise HTTPException(status_code=403, detail=denied.reason) from denied
    except tools.GatewayError as exc:
        # The gateway returns 409 for an already-resolved conflict; surface that
        # rather than reporting a success the caller did not get.
        status = 409 if "409" in str(exc) else 502
        raise HTTPException(status_code=status, detail=str(exc)) from exc

    memory_bank.remember(
        request.conflict_id, outcome="resolved", work_ids=[],
        detail=f"Resolved via {request.strategy}. {request.notes}".strip(),
    )
    return outcome


# ── Memory Bank (PRD §6.2) ───────────────────────────────────────

@app.get("/agents/memory")
async def list_memory():
    return {
        "backend": memory_bank.backend,
        "entries": memory_bank.all(),
        "count": len(memory_bank.all()),
    }


@app.get("/agents/memory/{conflict_id}")
async def recall_memory(conflict_id: str):
    entry = memory_bank.recall(conflict_id)
    if not entry:
        raise HTTPException(
            status_code=404, detail=f"No recollection of {conflict_id}."
        )
    return entry


@app.post("/agents/memory/reset")
async def reset_memory():
    """Clear cross-session recollection between demo takes."""
    return {"cleared": memory_bank.forget_all()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8002)))
