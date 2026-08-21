"""
DIYA Notice Service

Generates the real output artifacts for a resolved conflict: a public works
notice PDF and a closure calendar ICS (PRD §6.3). Artifacts are persisted to
Cloud Storage when configured, otherwise to a local volume.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator
from datetime import date

import artifacts
from storage import storage

app = FastAPI(
    title="DIYA Notice Service",
    description="Public works notice (PDF) and closure calendar (ICS) generation",
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


# ── Models ───────────────────────────────────────────────────────

class Phase(BaseModel):
    order: int = 0
    deptName: str = ""
    workType: str = ""
    start: str
    end: str
    rationale: str = ""


class NoticeRequest(BaseModel):
    conflict_id: str
    title: str
    description: str
    affected_area: str
    closure_start: str
    closure_end: str
    departments: list[str] = Field(default_factory=list)
    phases: list[Phase] = Field(default_factory=list)
    city: str = ""
    savings: int = 0

    @field_validator("closure_start", "closure_end")
    @classmethod
    def _iso_date(cls, value: str) -> str:
        # The previous implementation string-replaced hyphens straight into the
        # ICS, so a malformed date silently produced a corrupt calendar file.
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"Expected YYYY-MM-DD, got '{value}'") from exc
        return value


class NoticeResponse(BaseModel):
    notice_id: str
    conflict_id: str
    pdf_url: str
    ics_url: str
    pdf_uri: str
    ics_uri: str
    generated_at: str
    status: str
    storage_backend: str


# ── Routes ───────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"service": "DIYA Notice Service", "status": "operational", "version": "2.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy", "storage_backend": storage.backend}


@app.post("/notices/generate", response_model=NoticeResponse)
async def generate_notice(request: NoticeRequest):
    """Generate and persist both artifacts for a resolved conflict."""
    from datetime import datetime, timezone

    if date.fromisoformat(request.closure_end) < date.fromisoformat(request.closure_start):
        raise HTTPException(
            status_code=422, detail="closure_end must not precede closure_start"
        )

    notice_id = f"notice-{request.conflict_id}"
    phases = [p.model_dump() for p in request.phases]

    pdf_bytes = artifacts.build_pdf(
        notice_id=notice_id,
        title=request.title,
        description=request.description,
        affected_area=request.affected_area,
        closure_start=request.closure_start,
        closure_end=request.closure_end,
        departments=request.departments,
        phases=phases,
        city=request.city,
        savings=request.savings,
    )
    ics_bytes = artifacts.build_ics(
        notice_id=notice_id,
        title=request.title,
        description=request.description,
        affected_area=request.affected_area,
        closure_start=request.closure_start,
        closure_end=request.closure_end,
        departments=request.departments,
        phases=phases,
    )

    pdf_uri = storage.write(f"{notice_id}.pdf", pdf_bytes, "application/pdf")
    ics_uri = storage.write(f"{notice_id}.ics", ics_bytes, "text/calendar")

    return NoticeResponse(
        notice_id=notice_id,
        conflict_id=request.conflict_id,
        pdf_url=f"/notices/{notice_id}/pdf",
        ics_url=f"/notices/{notice_id}/ics",
        pdf_uri=pdf_uri,
        ics_uri=ics_uri,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        status="generated",
        storage_backend=storage.backend,
    )


@app.get("/notices/{notice_id}/pdf")
async def download_pdf(notice_id: str):
    data = storage.read(f"{notice_id}.pdf")
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No PDF for {notice_id}. POST /notices/generate first.",
        )
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{notice_id}.pdf"'},
    )


@app.get("/notices/{notice_id}/ics")
async def download_ics(notice_id: str):
    data = storage.read(f"{notice_id}.ics")
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No calendar for {notice_id}. POST /notices/generate first.",
        )
    return Response(
        content=data,
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="{notice_id}.ics"'},
    )


@app.get("/notices/{notice_id}/exists")
async def notice_exists(notice_id: str):
    return {
        "notice_id": notice_id,
        "pdf": storage.exists(f"{notice_id}.pdf"),
        "ics": storage.exists(f"{notice_id}.ics"),
        "storage_backend": storage.backend,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8003)))
