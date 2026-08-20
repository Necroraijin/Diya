"""
DIYA API Gateway
Central routing service for all DIYA microservices.
Handles request validation, routing, SSE event streaming, and CORS.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json
import asyncio


app = FastAPI(
    title="DIYA API Gateway",
    description="Multi-Agent Infrastructure Conflict Resolution System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Data Models ──────────────────────────────────────────────────

class ResolveRequest(BaseModel):
    resolution_type: str = "consolidated"
    notes: Optional[str] = None


class CitizenComplaint(BaseModel):
    text: str
    location: Optional[str] = None
    contact: Optional[str] = None


# ── Mock Data Store ──────────────────────────────────────────────

DEPARTMENTS = [
    {
        "id": "dept-roads",
        "name": "Roads & Bridges Department",
        "shortName": "Roads",
        "agentIdentityId": "agent-identity-roads-001",
        "color": "#ffffff",
        "icon": "road",
        "activeWorks": 12,
        "agentStatus": "online",
    },
    {
        "id": "dept-water",
        "name": "Water Supply & Sewerage Department",
        "shortName": "Water",
        "agentIdentityId": "agent-identity-water-001",
        "color": "#a0a0a0",
        "icon": "droplets",
        "activeWorks": 8,
        "agentStatus": "online",
    },
    {
        "id": "dept-telecom",
        "name": "Telecom & Fiber Infrastructure",
        "shortName": "Telecom",
        "agentIdentityId": "agent-identity-telecom-001",
        "color": "#666666",
        "icon": "wifi",
        "activeWorks": 15,
        "agentStatus": "processing",
    },
    {
        "id": "dept-sewage",
        "name": "Sewage & Drainage Department",
        "shortName": "Sewage",
        "agentIdentityId": "agent-identity-sewage-001",
        "color": "#444444",
        "icon": "waves",
        "activeWorks": 6,
        "agentStatus": "online",
    },
]

PLANNED_WORKS = [
    {
        "id": "pw-mum-001",
        "deptId": "dept-roads",
        "deptName": "Roads",
        "title": "SV Road Resurfacing - Andheri West",
        "description": "Complete bituminous resurfacing of SV Road from Andheri station junction to Juhu Circle.",
        "location": {"lat": 19.1197, "lng": 72.8464, "wayId": "way-48213001", "streetName": "SV Road", "ward": "K/W"},
        "geofenceRadius": 200,
        "startDate": "2026-09-15",
        "endDate": "2026-10-30",
        "workType": "Resurfacing",
        "status": "conflicted",
        "budget": 45000000,
        "city": "mumbai",
    },
    {
        "id": "pw-mum-004",
        "deptId": "dept-water",
        "deptName": "Water",
        "title": "Water Main Replacement - SV Road Segment",
        "description": "Replacement of 900mm CI water main along SV Road from DN Nagar to Irla Bridge.",
        "location": {"lat": 19.1185, "lng": 72.8451, "wayId": "way-48213001", "streetName": "SV Road", "ward": "K/W"},
        "geofenceRadius": 200,
        "startDate": "2026-10-01",
        "endDate": "2026-11-30",
        "workType": "Water Main Replacement",
        "status": "conflicted",
        "budget": 35000000,
        "city": "mumbai",
    },
    {
        "id": "pw-mum-006",
        "deptId": "dept-telecom",
        "deptName": "Telecom",
        "title": "OFC Laying - SV Road to Link Road",
        "description": "Optical fiber cable laying from SV Road junction through internal roads to Link Road.",
        "location": {"lat": 19.1201, "lng": 72.847, "wayId": "way-48213001", "streetName": "SV Road", "ward": "K/W"},
        "geofenceRadius": 150,
        "startDate": "2026-09-20",
        "endDate": "2026-10-20",
        "workType": "OFC Laying",
        "status": "conflicted",
        "budget": 12000000,
        "city": "mumbai",
    },
    {
        "id": "pw-mum-008",
        "deptId": "dept-sewage",
        "deptName": "Sewage",
        "title": "Storm Drain Upgrade - Andheri Subway",
        "description": "Upgrade of storm water drain capacity near Andheri subway.",
        "location": {"lat": 19.119, "lng": 72.8458, "wayId": "way-48213001", "streetName": "SV Road", "ward": "K/W"},
        "geofenceRadius": 180,
        "startDate": "2026-10-15",
        "endDate": "2026-12-15",
        "workType": "Storm Drain Upgrade",
        "status": "conflicted",
        "budget": 42000000,
        "city": "mumbai",
    },
    {
        "id": "pw-del-001",
        "deptId": "dept-roads",
        "deptName": "Roads",
        "title": "Chandni Chowk Road Restoration",
        "description": "Post-monsoon restoration of Chandni Chowk main road.",
        "location": {"lat": 28.6562, "lng": 77.231, "wayId": "way-92001001", "streetName": "Chandni Chowk Road", "ward": "Chandni Chowk"},
        "geofenceRadius": 200,
        "startDate": "2026-09-10",
        "endDate": "2026-10-25",
        "workType": "Restoration",
        "status": "conflicted",
        "budget": 38000000,
        "city": "delhi",
    },
    {
        "id": "pw-del-002",
        "deptId": "dept-water",
        "deptName": "Water",
        "title": "DJB Pipeline Relaying - Chandni Chowk",
        "description": "Relaying of aged 450mm DI pipeline under Chandni Chowk Road.",
        "location": {"lat": 28.6558, "lng": 77.2305, "wayId": "way-92001001", "streetName": "Chandni Chowk Road", "ward": "Chandni Chowk"},
        "geofenceRadius": 200,
        "startDate": "2026-09-25",
        "endDate": "2026-11-10",
        "workType": "Pipeline Relaying",
        "status": "conflicted",
        "budget": 25000000,
        "city": "delhi",
    },
]

CONFLICTS = [
    {
        "id": "conf-001",
        "workIds": ["pw-mum-001", "pw-mum-004", "pw-mum-006", "pw-mum-008"],
        "overlapType": "both",
        "proposedWindow": {"start": "2026-09-15", "end": "2026-12-15"},
        "status": "detected",
        "reasoningTrace": "Detected 4-way conflict on SV Road, Andheri West (Ward K/W). Proposed consolidated window: complete underground work first, then surface work.",
        "detectedAt": "2026-08-20T10:30:00Z",
        "severity": "critical",
        "savings": 32000000,
        "city": "mumbai",
    },
    {
        "id": "conf-002",
        "workIds": ["pw-del-001", "pw-del-002"],
        "overlapType": "both",
        "proposedWindow": {"start": "2026-09-10", "end": "2026-11-20"},
        "status": "detected",
        "reasoningTrace": "Detected conflict on Chandni Chowk Road. Roads restoration and DJB pipeline relaying target the same segment.",
        "detectedAt": "2026-08-20T11:15:00Z",
        "severity": "critical",
        "savings": 18000000,
        "city": "delhi",
    },
]

NOTICES = [
    {
        "id": "notice-001",
        "conflictId": "conf-003",
        "title": "Consolidated Road Works Notice - LBS Marg & BKC Area",
        "description": "Coordinated infrastructure works on LBS Marg and BKC connector roads.",
        "affectedArea": "LBS Marg (Kurla Terminus to Sion Junction) & BKC Connector Roads",
        "closureWindow": {"start": "2026-10-01", "end": "2026-12-30"},
        "departments": ["Roads & Bridges", "Telecom & Fiber"],
        "pdfUrl": "/notices/notice-001.pdf",
        "icsUrl": "/notices/notice-001.ics",
        "generatedAt": "2026-08-20T09:15:00Z",
        "status": "published",
    }
]

AGENT_ACTIVITIES = [
    {
        "id": "act-001",
        "agentName": "Coordinator Agent",
        "agentType": "coordinator",
        "action": "Conflict Detection",
        "detail": "Detected 4-way spatial+temporal conflict on SV Road, Andheri West.",
        "timestamp": "2026-08-20T10:30:00Z",
        "status": "success",
        "traceId": "trace-001",
        "duration": 8750,
    },
    {
        "id": "act-002",
        "agentName": "Coordinator Agent",
        "agentType": "coordinator",
        "action": "Cross-Department Read",
        "detail": "BLOCKED: Roads Agent attempted to read Water Department collection. Identity scope violation.",
        "timestamp": "2026-08-20T10:12:00Z",
        "status": "blocked",
        "duration": 45,
    },
    {
        "id": "act-003",
        "agentName": "Coordinator Agent",
        "agentType": "coordinator",
        "action": "Model Armor Check",
        "detail": "BLOCKED: Citizen complaint contained prompt injection attempt. Input sanitized.",
        "timestamp": "2026-08-20T08:45:00Z",
        "status": "blocked",
        "duration": 120,
    },
]


# ── Routes ───────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"service": "DIYA API Gateway", "status": "operational", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api-gateway": "up",
            "mesh-service": "up",
            "agent-service": "up",
            "notice-service": "up",
        },
    }


# ── Department Routes ────────────────────────────────────────────

@app.get("/api/departments")
async def list_departments():
    return {"departments": DEPARTMENTS, "count": len(DEPARTMENTS)}


@app.get("/api/departments/{dept_id}")
async def get_department(dept_id: str):
    dept = next((d for d in DEPARTMENTS if d["id"] == dept_id), None)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


# ── Planned Works Routes ─────────────────────────────────────────

@app.get("/api/planned-works")
async def list_planned_works(
    dept_id: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    works = PLANNED_WORKS
    if dept_id:
        works = [w for w in works if w["deptId"] == dept_id]
    if city:
        works = [w for w in works if w["city"] == city]
    if status:
        works = [w for w in works if w["status"] == status]
    return {"planned_works": works, "count": len(works)}


# ── Conflict Routes ──────────────────────────────────────────────

@app.get("/api/conflicts")
async def list_conflicts(
    status: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
):
    result = CONFLICTS
    if status:
        result = [c for c in result if c["status"] == status]
    if city:
        result = [c for c in result if c["city"] == city]
    return {"conflicts": result, "count": len(result)}


@app.get("/api/conflicts/{conflict_id}")
async def get_conflict(conflict_id: str):
    conflict = next((c for c in CONFLICTS if c["id"] == conflict_id), None)
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    # Attach full work objects
    works = [w for w in PLANNED_WORKS if w["id"] in conflict["workIds"]]
    return {**conflict, "works": works}


@app.post("/api/conflicts/{conflict_id}/resolve")
async def resolve_conflict(conflict_id: str, body: ResolveRequest):
    conflict = next((c for c in CONFLICTS if c["id"] == conflict_id), None)
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    conflict["status"] = "resolved"
    conflict["resolvedAt"] = datetime.utcnow().isoformat()
    return {
        "conflict_id": conflict_id,
        "status": "resolved",
        "resolution_type": body.resolution_type,
        "message": "Conflict resolved. Citizen Notice Agent triggered.",
    }


# ── Mesh Routes ──────────────────────────────────────────────────

@app.get("/api/mesh/{city}")
async def get_mesh_data(city: str):
    """Proxy to mesh-service — returns building and road geometry."""
    if city == "mumbai":
        return {
            "city": "mumbai",
            "center": [72.8777, 19.076],
            "zoom": 14,
            "buildings": 10,
            "roads": 5,
            "source": "osm-cache",
        }
    elif city == "delhi":
        return {
            "city": "delhi",
            "center": [77.2295, 28.6139],
            "zoom": 14,
            "buildings": 5,
            "roads": 2,
            "source": "osm-cache",
        }
    raise HTTPException(status_code=404, detail=f"City '{city}' not found. Available: mumbai, delhi")


# ── Notice Routes ────────────────────────────────────────────────

@app.get("/api/notices")
async def list_notices():
    return {"notices": NOTICES, "count": len(NOTICES)}


@app.get("/api/notices/{notice_id}")
async def get_notice(notice_id: str):
    notice = next((n for n in NOTICES if n["id"] == notice_id), None)
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    return notice


# ── Agent Routes ─────────────────────────────────────────────────

@app.get("/api/agents/activity")
async def agent_activity(
    agent_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    activities = AGENT_ACTIVITIES
    if agent_type:
        activities = [a for a in activities if a["agentType"] == agent_type]
    return {"activities": activities[:limit], "count": len(activities)}


@app.get("/api/agents/traces/{trace_id}")
async def get_trace(trace_id: str):
    return {
        "trace_id": trace_id,
        "agent": "Coordinator Agent",
        "conflict_id": "conf-001",
        "steps": [
            {"step": 1, "action": "Spatial Scan", "reasoning": "Scanning planned_works for geofence overlap.", "result": "4 records within 200m on SV Road", "duration": 1200},
            {"step": 2, "action": "Temporal Analysis", "reasoning": "Checking date window overlaps.", "result": "All 4 overlap Oct 1-20", "duration": 800},
            {"step": 3, "action": "Dependency Graph", "reasoning": "Building work-type sequence.", "result": "Sewer -> Water -> Telecom -> Roads", "duration": 2100},
            {"step": 4, "action": "Window Calculation", "reasoning": "Calculating consolidated window.", "result": "Sep 15 - Dec 15 with phased sub-windows", "duration": 1500},
            {"step": 5, "action": "Savings Estimation", "reasoning": "Estimating cost savings.", "result": "Rs 3.2 Crore estimated savings", "duration": 1150},
        ],
        "total_duration": 8750,
        "outcome": "CRITICAL conflict detected. 4-department consolidated window proposed.",
    }


# ── Citizen Complaint (Model Armor demo surface) ─────────────────

@app.post("/api/complaints")
async def submit_complaint(complaint: CitizenComplaint):
    """
    Public citizen complaint endpoint.
    This is the attack surface where Model Armor screens for prompt injection.
    """
    # Simple injection detection demo
    suspicious_patterns = ["ignore previous", "system prompt", "you are now", "disregard"]
    text_lower = complaint.text.lower()
    for pattern in suspicious_patterns:
        if pattern in text_lower:
            return {
                "status": "blocked",
                "reason": "Model Armor: potential prompt injection detected",
                "detail": f"Input contained suspicious pattern: '{pattern}'",
                "action": "Input sanitized before reaching any agent",
            }
    return {
        "status": "accepted",
        "message": "Complaint received and forwarded for processing",
        "complaint_id": f"cmp-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
    }


# ── SSE Events Stream ────────────────────────────────────────────

@app.get("/api/events")
async def event_stream():
    """Server-Sent Events stream for real-time updates to the frontend."""
    async def generate():
        while True:
            event = {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat(),
                "agents_online": 6,
                "active_conflicts": 2,
            }
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── Governance Routes ─────────────────────────────────────────────

@app.get("/api/governance/identity/verify")
async def verify_identity(
    agent_id: str = Query(...),
    resource: str = Query(...),
    action: str = Query("read"),
):
    """Agent Identity verification endpoint. Checks scope before data access."""
    # Parse agent scope from ID
    agent_dept = agent_id.split("-")[2] if len(agent_id.split("-")) > 2 else None
    resource_dept = resource.split("/")[0] if "/" in resource else resource

    # Coordinator has wildcard scope
    if "coordinator" in agent_id or agent_dept == "coordinator":
        return {
            "agent_id": agent_id,
            "resource": resource,
            "action": action,
            "result": "GRANTED",
            "reason": "Coordinator agent has wildcard read scope.",
            "scope": "*",
        }

    # Department agents can only access own scope
    if agent_dept and resource_dept and agent_dept != resource_dept:
        return {
            "agent_id": agent_id,
            "resource": resource,
            "action": action,
            "result": "DENIED",
            "reason": f"Scope violation: {agent_dept} agent cannot access {resource_dept} resources.",
            "scope": agent_dept,
        }

    return {
        "agent_id": agent_id,
        "resource": resource,
        "action": action,
        "result": "GRANTED",
        "reason": "Agent scope matches requested resource.",
        "scope": agent_dept or "unknown",
    }


@app.post("/api/governance/armor/scan")
async def armor_scan(complaint: CitizenComplaint):
    """Model Armor scan endpoint — screens input for threats."""
    suspicious_patterns = {
        "ignore previous": "prompt_injection",
        "ignore all": "prompt_injection",
        "system prompt": "prompt_injection",
        "you are now": "jailbreak",
        "disregard": "prompt_injection",
        "dan": "jailbreak",
        "pretend": "jailbreak",
        "api key": "data_exfiltration",
        "password": "data_exfiltration",
        "database": "data_exfiltration",
        "connection string": "data_exfiltration",
        "reveal": "data_exfiltration",
    }
    text_lower = complaint.text.lower()
    detected = []
    for pattern, threat_type in suspicious_patterns.items():
        if pattern in text_lower:
            detected.append({"pattern": pattern, "type": threat_type})

    if detected:
        return {
            "status": "blocked",
            "severity": "critical" if len(detected) > 1 else "high",
            "threats": detected,
            "threat_count": len(detected),
            "sanitized_output": "[BLOCKED] Input contained malicious patterns.",
            "detail": f"Model Armor detected {len(detected)} threat pattern(s). Input blocked.",
        }
    return {
        "status": "passed",
        "severity": "none",
        "threats": [],
        "threat_count": 0,
        "detail": "No threats detected. Input cleared for agent processing.",
    }


@app.get("/api/governance/stats")
async def governance_stats():
    """Governance dashboard statistics."""
    return {
        "identity_checks": {"total": 234, "granted": 211, "denied": 23},
        "armor_scans": {"total": 847, "blocked": 23, "passed": 824},
        "runtime": {
            "max_turns": 10,
            "timeout_seconds": 30,
            "rate_limit_per_min": 100,
            "circuit_breaker_threshold": 5,
        },
        "agents_registered": 6,
        "agents_online": 6,
    }


# ── Dashboard Metrics ─────────────────────────────────────────────

@app.get("/api/dashboard/metrics")
async def dashboard_metrics():
    return {
        "totalConflicts": len(CONFLICTS),
        "resolvedConflicts": len([c for c in CONFLICTS if c["status"] == "resolved"]),
        "activeWorks": len(PLANNED_WORKS),
        "departments": len(DEPARTMENTS),
        "estimatedSavings": sum(c["savings"] for c in CONFLICTS),
        "citizenNotices": len(NOTICES),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
