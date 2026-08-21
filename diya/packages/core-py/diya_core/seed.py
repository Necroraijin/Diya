"""
Seed loading.

`data/synthetic/*.json` is the single source of truth for the demo dataset.
Previously departments/works/conflicts were defined independently in the
frontend mock file, the api-gateway module and these JSON files; this loader
makes the JSON canonical for every Python service.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from diya_core.models import Conflict, Department, Location, PlannedWork

# Presentation metadata that does not belong in the source data files.
_DEPT_PRESENTATION: dict[str, tuple[str, str, str]] = {
    "dept-roads": ("Roads", "#ffffff", "road"),
    "dept-water": ("Water", "#a0a0a0", "droplets"),
    "dept-telecom": ("Telecom", "#666666", "wifi"),
    "dept-sewage": ("Sewage", "#444444", "waves"),
}
_DEFAULT_PRESENTATION = ("Dept", "#888888", "building")


class SeedData(BaseModel):
    departments: list[Department]
    works: list[PlannedWork]
    # Stable ids for the hand-authored conflicts, keyed by their work-id set.
    known_conflict_ids: dict[frozenset[str], str]
    seeded_conflicts: list[dict]

    model_config = {"arbitrary_types_allowed": True}


def data_dir() -> Path:
    """
    Resolve the synthetic data directory.

    Honours DIYA_DATA_DIR first (set in the container images), then walks up
    from this file looking for `data/synthetic` so local runs work from any cwd.
    """
    override = os.environ.get("DIYA_DATA_DIR")
    if override:
        return Path(override)

    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data" / "synthetic"
        if candidate.is_dir():
            return candidate

    raise FileNotFoundError(
        "Could not locate data/synthetic. Set DIYA_DATA_DIR to its absolute path."
    )


def _department(raw: dict) -> Department:
    short, color, icon = _DEPT_PRESENTATION.get(raw["id"], _DEFAULT_PRESENTATION)
    return Department(
        id=raw["id"],
        name=raw["name"],
        shortName=short,
        agentIdentityId=raw["agent_identity_id"],
        ulbReference=raw.get("ulb_reference"),
        color=color,
        icon=icon,
    )


def _planned_work(raw: dict, city: str, dept_names: dict[str, str]) -> PlannedWork:
    loc = raw["location"]
    short, _, _ = _DEPT_PRESENTATION.get(raw["dept_id"], _DEFAULT_PRESENTATION)
    return PlannedWork(
        id=raw["id"],
        deptId=raw["dept_id"],
        deptName=short,
        title=raw["title"],
        description=raw["description"],
        location=Location(
            lat=loc["lat"],
            lng=loc["lng"],
            wayId=loc["way_id"],
            streetName=loc["street_name"],
            ward=loc["ward"],
            landmark=loc.get("landmark"),
        ),
        geofenceRadius=raw["geofence_radius_m"],
        startDate=raw["start_date"],
        endDate=raw["end_date"],
        workType=raw["work_type"],
        status="planned",
        budget=raw.get("estimated_budget_inr", 0),
        city=city,
        trafficImpact=raw.get("traffic_impact"),
    )


@lru_cache(maxsize=1)
def load_seed(directory: Optional[str] = None) -> SeedData:
    """Load and normalise every city file in the data directory. Cached."""
    base = Path(directory) if directory else data_dir()

    departments: dict[str, Department] = {}
    works: list[PlannedWork] = []
    known_ids: dict[frozenset[str], str] = {}
    seeded: list[dict] = []

    for path in sorted(base.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        city = payload["city"]

        for raw in payload.get("departments", []):
            if raw["id"] not in departments:
                departments[raw["id"]] = _department(raw)

        dept_names = {d.id: d.name for d in departments.values()}
        for raw in payload.get("planned_works", []):
            works.append(_planned_work(raw, city, dept_names))

        for raw in payload.get("seeded_conflicts", []):
            known_ids[frozenset(raw["work_ids"])] = raw["id"]
            seeded.append({**raw, "city": city})

    # activeWorks is derived, never hand-maintained.
    for dept in departments.values():
        dept.activeWorks = sum(1 for w in works if w.deptId == dept.id)

    return SeedData(
        departments=list(departments.values()),
        works=works,
        known_conflict_ids=known_ids,
        seeded_conflicts=seeded,
    )
