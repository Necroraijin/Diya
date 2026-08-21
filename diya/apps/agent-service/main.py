"""
DIYA Agent Service

Describes the agent fleet and hosts the ADK orchestration.

Phase 2 status: the deterministic conflict detector lives in
`diya_core.conflict` and is driven by the gateway (POST /api/conflicts/detect).
The ADK Department/Coordinator/Notice agents land in Phase 3 and will call that
same module as tools, so the reasoning trace stays grounded in real arithmetic.

The orchestration endpoints below therefore return 501 rather than fabricated
success payloads — a stub that lies about having run an agent is worse than one
that says it has not been built yet.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from diya_core.models import utcnow_iso
from diya_core.seed import load_seed

app = FastAPI(
    title="DIYA Agent Service",
    description="ADK agent fleet — orchestration lands in Phase 3",
    version="2.0.0",
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

PHASE_3_DETAIL = (
    "ADK agent orchestration is Phase 3. The deterministic detector is live at "
    f"POST {GATEWAY_URL}/api/conflicts/detect and produces the same conflict "
    "records and reasoning traces this endpoint will return once wired to ADK."
)


class IngestRequest(BaseModel):
    dept_id: str
    feed_source: Optional[str] = None


class ResolutionRequest(BaseModel):
    conflict_id: str
    strategy: str = "consolidated"
    max_turns: int = MAX_TURNS


@app.get("/")
async def root():
    return {"service": "DIYA Agent Service", "status": "operational", "version": "2.0.0"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "adk_wired": False,
        "phase": "2 — fleet described, orchestration pending",
    }


@app.get("/agents/status")
async def agents_status():
    """
    The agent fleet, derived from the seeded departments.

    One Department Agent per department, each with its own Agent Identity, plus
    the Coordinator and the Citizen Notice Agent (PRD §6).
    """
    seed = load_seed()

    agents = [
        {
            "name": f"{d.shortName} Department Agent",
            "type": "department",
            "identityId": d.agentIdentityId,
            "scope": f"departments/{d.id}/**",
            "crossDepartmentRead": False,
            "status": "online",
            "recordsInScope": d.activeWorks,
            "adkWired": False,
        }
        for d in seed.departments
    ]

    agents.append({
        "name": "Coordinator Agent",
        "type": "coordinator",
        "identityId": "agent-identity-coordinator-001",
        "scope": "departments/**",
        # The single elevated identity in the system — PRD §6.2.
        "crossDepartmentRead": True,
        "status": "online",
        "recordsInScope": len(seed.works),
        "maxTurns": MAX_TURNS,
        "adkWired": False,
    })
    agents.append({
        "name": "Citizen Notice Agent",
        "type": "notice",
        "identityId": "agent-identity-notice-001",
        "scope": "conflicts/**:read, notices/**:write",
        "crossDepartmentRead": False,
        "status": "online",
        "adkWired": False,
    })

    return {
        "agents": agents,
        "count": len(agents),
        "timestamp": utcnow_iso(),
        "orchestration": "pending-phase-3",
    }


@app.post("/agents/department/ingest")
async def ingest_department_feed(request: IngestRequest):
    raise HTTPException(status_code=501, detail=PHASE_3_DETAIL)


@app.post("/agents/coordinator/detect")
async def detect_conflicts():
    raise HTTPException(status_code=501, detail=PHASE_3_DETAIL)


@app.post("/agents/coordinator/resolve")
async def resolve_conflict(request: ResolutionRequest):
    raise HTTPException(status_code=501, detail=PHASE_3_DETAIL)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8002)))
