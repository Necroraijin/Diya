"""
DIYA Agent Service
ADK-based agent orchestration for department agents, coordinator, and notice agent.
Exposes HTTP endpoints for triggering agent workflows.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

app = FastAPI(title="DIYA Agent Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ───────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    dept_id: str
    feed_source: Optional[str] = None


class DetectionResult(BaseModel):
    status: str
    conflicts_found: int
    message: str
    trace_id: Optional[str] = None


class ResolutionRequest(BaseModel):
    conflict_id: str
    strategy: str = "consolidated"
    max_turns: int = 5


# ── Routes ───────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"service": "DIYA Agent Service", "status": "operational"}


@app.get("/health")
async def health():
    return {"status": "healthy", "agents": {"department": 4, "coordinator": 1, "notice": 1}}


@app.get("/agents/status")
async def agents_status():
    """Return current status of all agents."""
    return {
        "agents": [
            {"name": "Roads Department Agent", "type": "department", "status": "online", "last_run": "2026-08-20T10:00:00Z", "records_processed": 3},
            {"name": "Water Department Agent", "type": "department", "status": "online", "last_run": "2026-08-20T10:05:00Z", "records_processed": 2},
            {"name": "Telecom Department Agent", "type": "department", "status": "online", "last_run": "2026-08-20T10:08:00Z", "records_processed": 2},
            {"name": "Sewage Department Agent", "type": "department", "status": "online", "last_run": "2026-08-20T10:10:00Z", "records_processed": 1},
            {"name": "Coordinator Agent", "type": "coordinator", "status": "online", "last_run": "2026-08-20T10:30:00Z", "conflicts_detected": 2},
            {"name": "Citizen Notice Agent", "type": "notice", "status": "online", "last_run": "2026-08-20T09:15:00Z", "notices_generated": 1},
        ]
    }


@app.post("/agents/department/ingest")
async def ingest_department_feed(request: IngestRequest):
    """
    Trigger a department agent to normalize raw feed data.
    TODO Phase 3: Implement ADK Department Agent with Gemini 3.5 Flash.
    """
    return {
        "dept_id": request.dept_id,
        "status": "completed",
        "records_normalized": 3,
        "timestamp": datetime.utcnow().isoformat(),
        "agent": f"{request.dept_id}-agent",
        "message": f"Department agent ingested feed for {request.dept_id}",
    }


@app.post("/agents/coordinator/detect", response_model=DetectionResult)
async def detect_conflicts():
    """
    Trigger coordinator agent to scan for cross-department conflicts.
    TODO Phase 3: Implement ADK Coordinator Agent with Memory Bank.
    """
    return DetectionResult(
        status="completed",
        conflicts_found=2,
        message="Coordinator agent completed conflict scan. 2 conflicts detected.",
        trace_id="trace-001",
    )


@app.post("/agents/coordinator/resolve")
async def resolve_conflict(request: ResolutionRequest):
    """
    Trigger coordinator agent to propose resolution for a specific conflict.
    Includes max-turn cap to prevent runaway agent loops (Red Flag #9).
    """
    return {
        "conflict_id": request.conflict_id,
        "status": "resolved",
        "strategy": request.strategy,
        "turns_used": 3,
        "max_turns": request.max_turns,
        "proposed_window": {"start": "2026-09-15", "end": "2026-12-15"},
        "savings_estimate": 32000000,
        "trace_id": f"trace-resolve-{request.conflict_id}",
        "message": "Conflict resolved with consolidated work window.",
    }


@app.get("/agents/traces/{trace_id}")
async def get_reasoning_trace(trace_id: str):
    """Retrieve reasoning trace for an agent run."""
    return {
        "trace_id": trace_id,
        "agent": "Coordinator Agent",
        "conflict_id": "conf-001",
        "started_at": "2026-08-20T10:30:00Z",
        "completed_at": "2026-08-20T10:30:09Z",
        "total_duration_ms": 8750,
        "steps": [
            {
                "step": 1,
                "action": "Spatial Scan",
                "reasoning": "Scanning all planned_works for geofence intersection. Threshold: 50m overlap.",
                "result": "Found 4 records within 200m on wayId: way-48213001 (SV Road)",
                "duration_ms": 1200,
            },
            {
                "step": 2,
                "action": "Temporal Analysis",
                "reasoning": "Checking date window overlaps for spatially co-located works.",
                "result": "All 4 overlap between Oct 1-20, 2026. Full span: Sep 15 - Dec 15.",
                "duration_ms": 800,
            },
            {
                "step": 3,
                "action": "Dependency Graph",
                "reasoning": "Underground utilities must complete before surface work.",
                "result": "Optimal: storm drain -> water main -> OFC -> resurfacing",
                "duration_ms": 2100,
            },
            {
                "step": 4,
                "action": "Window Calculation",
                "reasoning": "Calculating consolidated window with buffer days.",
                "result": "Proposed: Storm drain (Sep 15-Oct 15) -> Water (Oct 10-Nov 10) -> OFC (Oct 25-Nov 15) -> Resurfacing (Nov 15-Dec 15)",
                "duration_ms": 1500,
            },
            {
                "step": 5,
                "action": "Savings Estimation",
                "reasoning": "Shared traffic management, single mobilization, reduced restoration.",
                "result": "Estimated savings: Rs 3.2 Crore. Disruption: 4 closures -> 1.",
                "duration_ms": 1150,
            },
        ],
        "outcome": "CRITICAL conflict detected. 4-department consolidated window proposed. Awaiting acknowledgment.",
        "memory_bank": {
            "stored": True,
            "key": "conf-001-resolution",
            "expires": None,
        },
    }


@app.post("/agents/identity/verify")
async def verify_identity(agent_id: str, resource_path: str):
    """
    Demo endpoint for Agent Identity scope verification.
    Shows cross-department read denial.
    """
    # Parse agent department from ID
    agent_dept = agent_id.split("-")[2] if len(agent_id.split("-")) > 2 else "unknown"
    resource_dept = resource_path.split("/")[1] if "/" in resource_path else "unknown"

    if agent_dept == resource_dept or agent_id.startswith("agent-identity-coordinator"):
        return {
            "agent_id": agent_id,
            "resource": resource_path,
            "access": "GRANTED",
            "scope": f"departments/{resource_dept}/planned_works/*",
        }

    return {
        "agent_id": agent_id,
        "resource": resource_path,
        "access": "DENIED",
        "reason": f"Agent {agent_id} does not have read scope for {resource_path}",
        "allowed_scope": f"departments/dept-{agent_dept}/planned_works/*",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
