"""
DIYA Notice Service
Generates PDF public works notices and ICS calendar files for resolved conflicts.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os

app = FastAPI(title="DIYA Notice Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/app/output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class NoticeRequest(BaseModel):
    conflict_id: str
    title: str
    description: str
    affected_area: str
    closure_start: str
    closure_end: str
    departments: list[str]


class NoticeResponse(BaseModel):
    notice_id: str
    conflict_id: str
    pdf_url: str
    ics_url: str
    generated_at: str
    status: str


@app.get("/")
async def root():
    return {"service": "DIYA Notice Service", "status": "operational"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/notices/generate", response_model=NoticeResponse)
async def generate_notice(request: NoticeRequest):
    """
    Generate PDF notice and ICS calendar file for a resolved conflict.
    TODO Phase 3: Implement with ReportLab for PDF and icalendar for ICS.
    Currently returns mock response with valid structure.
    """
    notice_id = f"notice-{request.conflict_id}"
    generated_at = datetime.utcnow().isoformat() + "Z"

    # Generate ICS content (this works without any extra library)
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//DIYA//Infrastructure Conflict Resolution//EN
BEGIN:VEVENT
DTSTART:{request.closure_start.replace('-', '')}T000000Z
DTEND:{request.closure_end.replace('-', '')}T235959Z
SUMMARY:{request.title}
DESCRIPTION:{request.description}
LOCATION:{request.affected_area}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""

    ics_path = os.path.join(OUTPUT_DIR, f"{notice_id}.ics")
    with open(ics_path, "w") as f:
        f.write(ics_content)

    return NoticeResponse(
        notice_id=notice_id,
        conflict_id=request.conflict_id,
        pdf_url=f"/notices/{notice_id}/pdf",
        ics_url=f"/notices/{notice_id}/ics",
        generated_at=generated_at,
        status="generated",
    )


@app.get("/notices/{notice_id}/ics")
async def download_ics(notice_id: str):
    """Download generated ICS calendar file."""
    ics_path = os.path.join(OUTPUT_DIR, f"{notice_id}.ics")
    if os.path.exists(ics_path):
        return FileResponse(
            ics_path,
            media_type="text/calendar",
            filename=f"{notice_id}.ics",
        )

    # Return a sample ICS if file doesn't exist yet
    sample_ics = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//DIYA//Infrastructure Conflict Resolution//EN
BEGIN:VEVENT
DTSTART:20261001T000000Z
DTEND:20261230T235959Z
SUMMARY:Consolidated Road Works - LBS Marg & BKC Area
DESCRIPTION:Coordinated infrastructure works. Traffic diversions coordinated.
LOCATION:LBS Marg (Kurla) & BKC Connector Roads
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""

    return Response(
        content=sample_ics,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename={notice_id}.ics"},
    )


@app.get("/notices/{notice_id}/pdf")
async def download_pdf(notice_id: str):
    """Download generated PDF notice. TODO: Implement with ReportLab."""
    pdf_path = os.path.join(OUTPUT_DIR, f"{notice_id}.pdf")
    if os.path.exists(pdf_path):
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"{notice_id}.pdf",
        )

    raise HTTPException(
        status_code=404,
        detail=f"PDF for {notice_id} not yet generated. Call POST /notices/generate first.",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
