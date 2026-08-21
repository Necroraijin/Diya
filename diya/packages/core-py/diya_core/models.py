"""
Domain models.

Field names are camelCase to match `apps/web/src/types/index.ts` exactly, so a
model dumped with `.model_dump()` is directly consumable by the frontend with
no transformation layer in between.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

AgentStatus = Literal["online", "offline", "processing"]
WorkStatus = Literal["planned", "in-progress", "completed", "conflicted"]
OverlapType = Literal["spatial", "temporal", "both"]
ConflictStatus = Literal["detected", "resolved", "dismissed"]
Severity = Literal["critical", "high", "medium", "low"]
NoticeStatus = Literal["draft", "published", "expired"]


def utcnow() -> datetime:
    """Timezone-aware UTC now. `datetime.utcnow()` is deprecated in 3.12+."""
    return datetime.now(timezone.utc)


def utcnow_iso() -> str:
    return utcnow().isoformat().replace("+00:00", "Z")


class Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class Location(Base):
    lat: float
    lng: float
    wayId: str
    streetName: str
    ward: str
    landmark: Optional[str] = None


class Department(Base):
    id: str
    name: str
    shortName: str
    agentIdentityId: str
    ulbReference: Optional[str] = None
    color: str = "#ffffff"
    icon: str = "building"
    activeWorks: int = 0
    agentStatus: AgentStatus = "online"


class PlannedWork(Base):
    id: str
    deptId: str
    deptName: str
    title: str
    description: str
    location: Location
    geofenceRadius: int
    startDate: str
    endDate: str
    workType: str
    status: WorkStatus = "planned"
    budget: int = 0
    city: str
    trafficImpact: Optional[str] = None

    @property
    def start(self) -> date:
        return date.fromisoformat(self.startDate)

    @property
    def end(self) -> date:
        return date.fromisoformat(self.endDate)


class WindowPhase(Base):
    """One sequenced sub-window inside a consolidated closure."""

    workId: str
    deptName: str
    workType: str
    start: str
    end: str
    order: int
    rationale: str


class ProposedWindow(Base):
    start: str
    end: str
    phases: list[WindowPhase] = Field(default_factory=list)


class ReasoningStep(Base):
    step: int
    action: str
    reasoning: str
    result: str
    durationMs: int = 0


class Conflict(Base):
    id: str
    workIds: list[str]
    overlapType: OverlapType
    proposedWindow: ProposedWindow
    status: ConflictStatus = "detected"
    reasoningTrace: str
    reasoningSteps: list[ReasoningStep] = Field(default_factory=list)
    detectedAt: str = Field(default_factory=utcnow_iso)
    resolvedAt: Optional[str] = None
    severity: Severity = "medium"
    savings: int = 0
    city: str
    locationSummary: str = ""
    traceId: Optional[str] = None


class Notice(Base):
    id: str
    conflictId: str
    title: str
    description: str
    affectedArea: str
    closureWindow: ProposedWindow
    departments: list[str]
    pdfUrl: str
    icsUrl: str
    generatedAt: str = Field(default_factory=utcnow_iso)
    status: NoticeStatus = "published"


class AgentActivity(Base):
    id: str
    agentName: str
    agentType: Literal["department", "coordinator", "notice", "governance"]
    action: str
    detail: str
    timestamp: str = Field(default_factory=utcnow_iso)
    status: Literal["success", "error", "processing", "blocked"] = "success"
    traceId: Optional[str] = None
    duration: Optional[int] = None
