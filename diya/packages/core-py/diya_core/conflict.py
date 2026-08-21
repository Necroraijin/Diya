"""
Conflict detection.

This is the core algorithm of the product: given a set of PlannedWork records
across departments, find groups of works that will dig up the same ground, and
propose a single consolidated closure window that sequences them correctly.

The reasoning trace produced here is *derived*, not narrated — every number in
it comes from the computation. Phase 3 replaces this module's invocation with an
ADK Coordinator Agent that calls the same functions as tools, so the trace stays
grounded in real arithmetic rather than model prose.
"""

from __future__ import annotations

import itertools
from datetime import date, timedelta
from typing import Iterable, Optional

from pydantic import BaseModel

from diya_core.geo import geofences_intersect
from diya_core.models import (
    Conflict,
    OverlapType,
    PlannedWork,
    ProposedWindow,
    ReasoningStep,
    Severity,
    WindowPhase,
    utcnow_iso,
)


class DetectionConfig(BaseModel):
    """Tunable thresholds for detection. Defaults are the demo-tuned values."""

    # Two works count as a "repeat dig" even without calendar overlap if they
    # fall within this many days of each other — resurfacing in March and
    # trenching in June is exactly the failure this product exists to prevent.
    repeat_dig_window_days: int = 365
    # Minimum geofence penetration before we call it a real spatial conflict.
    # Guards against two works that merely graze each other's radius.
    min_overlap_depth_m: float = 25.0
    # Days of slack inserted between consolidated phases (crew demobilisation,
    # backfill settling, inspection).
    phase_buffer_days: int = 3
    # How far into a phase the next trade may begin. Real consolidated digs run
    # trades in a rolling sequence along the trench rather than strictly one
    # after another; 0.0 would mean fully sequential, 1.0 fully concurrent.
    phase_overlap_ratio: float = 0.6
    # Share of a work's budget attributable to site mobilisation, avoided when
    # the work joins an existing consolidated dig.
    mobilisation_fraction: float = 0.06
    # Share attributable to surface restoration (repaving, marking), avoided for
    # every work except the one that resurfaces last.
    restoration_fraction: float = 0.10


# Excavation depth ordering. Deepest utility goes first so that no later work
# has to re-open ground that has already been restored. Higher rank == earlier.
_DEPTH_RANK: list[tuple[tuple[str, ...], int, str]] = [
    (("storm drain", "sewage", "sewer", "drainage"), 40, "deepest excavation — storm/sewer inverts sit below all other utilities"),
    (("water main", "pipeline", "water"), 30, "water mains sit above sewers but below shallow utilities"),
    (("ofc", "fiber", "fibre", "telecom", "cable", "5g"), 20, "shallow duct trenching, must precede surface works"),
    (("resurfacing", "restoration", "widening", "structural", "road"), 10, "surface work must be last so it is not re-opened"),
]
_DEFAULT_RANK = 25
_DEFAULT_RATIONALE = "unclassified work type — sequenced by planned start date"

# Human-readable phrasing for overlap types, used anywhere a trace or notice is
# read by a person rather than matched by code.
_OVERLAP_LABEL: dict[str, str] = {
    "both": "spatial and temporal",
    "spatial": "spatial (repeat-dig)",
    "temporal": "temporal",
}


def depth_rank(work: PlannedWork) -> tuple[int, str]:
    """Rank a work by excavation depth, with the reason for that ranking."""
    haystack = f"{work.workType} {work.title}".lower()
    for keywords, rank, rationale in _DEPTH_RANK:
        if any(k in haystack for k in keywords):
            return rank, rationale
    return _DEFAULT_RANK, _DEFAULT_RATIONALE


def _date_ranges_overlap(a: PlannedWork, b: PlannedWork) -> tuple[bool, int]:
    """Whether two work windows overlap, and by how many days (or the gap, negative)."""
    latest_start = max(a.start, b.start)
    earliest_end = min(a.end, b.end)
    delta = (earliest_end - latest_start).days
    return delta >= 0, delta


class _UnionFind:
    def __init__(self, items: Iterable[str]) -> None:
        self.parent = {i: i for i in items}

    def find(self, x: str) -> str:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra

    def groups(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for item in self.parent:
            out.setdefault(self.find(item), []).append(item)
        return out


class PairOverlap(BaseModel):
    work1: str
    work2: str
    distanceM: float
    overlapDepthM: float
    sameWayId: bool
    temporalOverlap: bool
    temporalDeltaDays: int
    overlapType: OverlapType


def analyse_pairs(
    works: list[PlannedWork], config: Optional[DetectionConfig] = None
) -> list[PairOverlap]:
    """Every qualifying pairwise conflict among the supplied works."""
    cfg = config or DetectionConfig()
    pairs: list[PairOverlap] = []

    for a, b in itertools.combinations(works, 2):
        if a.city != b.city:
            continue
        # Two works from the same department are that department's own
        # scheduling problem, not a cross-department dig-once conflict.
        if a.deptId == b.deptId:
            continue

        intersects, distance, depth = geofences_intersect(
            a.location.lat, a.location.lng, a.geofenceRadius,
            b.location.lat, b.location.lng, b.geofenceRadius,
        )
        same_way = a.location.wayId == b.location.wayId
        # A shared OSM way id is direct evidence of the same road segment even
        # if the recorded centroids sit far apart.
        if not (intersects and depth >= cfg.min_overlap_depth_m) and not same_way:
            continue

        temporal, delta = _date_ranges_overlap(a, b)
        if not temporal and abs(delta) > cfg.repeat_dig_window_days:
            continue

        pairs.append(
            PairOverlap(
                work1=a.id,
                work2=b.id,
                distanceM=round(distance, 1),
                overlapDepthM=round(depth, 1),
                sameWayId=same_way,
                temporalOverlap=temporal,
                temporalDeltaDays=delta,
                overlapType="both" if temporal else "spatial",
            )
        )

    return pairs


def _consolidate(
    works: list[PlannedWork], cfg: DetectionConfig
) -> ProposedWindow:
    """
    Sequence the works deepest-first into one closure window.

    Each work keeps its original duration. A trade may start once the preceding
    trade is `phase_overlap_ratio` complete, plus a buffer — a rolling sequence
    along the trench rather than four strictly serial closures.
    """
    ordered = sorted(
        works,
        key=lambda w: (-depth_rank(w)[0], w.start),
    )
    phases: list[WindowPhase] = []
    phase_start = min(w.start for w in works)

    for index, work in enumerate(ordered, start=1):
        duration = (work.end - work.start).days
        phase_end = phase_start + timedelta(days=duration)
        _, rationale = depth_rank(work)
        phases.append(
            WindowPhase(
                workId=work.id,
                deptName=work.deptName,
                workType=work.workType,
                start=phase_start.isoformat(),
                end=phase_end.isoformat(),
                order=index,
                rationale=rationale,
            )
        )
        phase_start = phase_start + timedelta(
            days=int(duration * cfg.phase_overlap_ratio) + cfg.phase_buffer_days
        )

    return ProposedWindow(
        start=phases[0].start,
        end=max(p.end for p in phases),
        phases=phases,
    )


def _estimate_savings(works: list[PlannedWork], cfg: DetectionConfig) -> tuple[int, str]:
    """
    Cost avoided by digging once instead of N times.

    Model: the deepest work bears full mobilisation and the final surface work
    bears full restoration. Every other work avoids its own mobilisation, and
    every work except the last avoids its own surface restoration.
    """
    ordered = sorted(works, key=lambda w: -depth_rank(w)[0])
    mobilisation_saved = sum(
        w.budget * cfg.mobilisation_fraction for w in ordered[1:]
    )
    restoration_saved = sum(
        w.budget * cfg.restoration_fraction for w in ordered[:-1]
    )
    total = int(mobilisation_saved + restoration_saved)
    explanation = (
        f"{len(ordered) - 1} avoided mobilisation(s) at {cfg.mobilisation_fraction:.0%} "
        f"= Rs {int(mobilisation_saved):,}; "
        f"{len(ordered) - 1} avoided surface restoration(s) at {cfg.restoration_fraction:.0%} "
        f"= Rs {int(restoration_saved):,}"
    )
    return total, explanation


def _severity(work_count: int, overlap_type: OverlapType) -> Severity:
    if work_count >= 4 or (work_count >= 3 and overlap_type == "both"):
        return "critical"
    if work_count == 3 or overlap_type == "both":
        return "high"
    return "medium"


def _build_steps(
    works: list[PlannedWork],
    pairs: list[PairOverlap],
    window: ProposedWindow,
    savings: int,
    savings_explanation: str,
    cfg: DetectionConfig,
) -> list[ReasoningStep]:
    closest = min(pairs, key=lambda p: p.distanceM)
    temporal_pairs = [p for p in pairs if p.temporalOverlap]
    ways = sorted({w.location.wayId for w in works})
    depts = sorted({w.deptName for w in works})
    order = " -> ".join(p.workType for p in window.phases)

    original_days = sum((w.end - w.start).days for w in works)
    consolidated_days = (
        date.fromisoformat(window.end) - date.fromisoformat(window.start)
    ).days

    return [
        ReasoningStep(
            step=1,
            action="Spatial Scan",
            reasoning=(
                f"Compared geofences pairwise using haversine distance. A pair qualifies "
                f"when circles penetrate by at least {cfg.min_overlap_depth_m:.0f}m or "
                f"share an OSM way id."
            ),
            result=(
                f"{len(works)} works across {len(depts)} departments on way(s) "
                f"{', '.join(ways)}. Closest pair {closest.work1}/{closest.work2} at "
                f"{closest.distanceM}m (penetration {closest.overlapDepthM}m)."
            ),
        ),
        ReasoningStep(
            step=2,
            action="Temporal Analysis",
            reasoning=(
                f"Intersected date windows for spatially co-located works. Non-overlapping "
                f"pairs still qualify inside the {cfg.repeat_dig_window_days}-day repeat-dig window."
            ),
            result=(
                f"{len(temporal_pairs)} of {len(pairs)} pairs overlap on the calendar. "
                f"Full span {min(w.startDate for w in works)} to {max(w.endDate for w in works)}."
            ),
        ),
        ReasoningStep(
            step=3,
            action="Dependency Graph",
            reasoning=(
                "Ranked works by excavation depth so that no later work re-opens ground "
                "already restored by an earlier one."
            ),
            result=f"Execution order: {order}",
        ),
        ReasoningStep(
            step=4,
            action="Window Calculation",
            reasoning=(
                f"Sequenced each work at its original duration, each trade starting at "
                f"{cfg.phase_overlap_ratio:.0%} completion of the previous one plus a "
                f"{cfg.phase_buffer_days}-day buffer, from the earliest planned start."
            ),
            result=(
                f"Consolidated window {window.start} to {window.end} "
                f"({consolidated_days} days, {len(window.phases)} phases). "
                f"Cumulative closure-days fall from {original_days} across "
                f"{len(works)} separate closures to {consolidated_days} in 1 "
                f"({1 - consolidated_days / original_days:.0%} reduction)."
                if consolidated_days < original_days
                else
                f"Consolidated window {window.start} to {window.end} "
                f"({consolidated_days} days, {len(window.phases)} phases) versus "
                f"{original_days} cumulative closure-days across {len(works)} "
                f"separate closures."
            ),
        ),
        ReasoningStep(
            step=5,
            action="Savings Estimation",
            reasoning=savings_explanation,
            result=(
                f"Estimated saving Rs {savings:,} "
                f"(Rs {savings / 10_000_000:.2f} Crore). "
                f"Citizen disruption: {len(works)} closures -> 1."
            ),
        ),
    ]


def detect_conflicts(
    works: list[PlannedWork],
    config: Optional[DetectionConfig] = None,
    known_ids: Optional[dict[frozenset[str], str]] = None,
) -> list[Conflict]:
    """
    Detect all cross-department conflicts among `works`.

    `known_ids` maps a frozenset of work ids to a stable conflict id, so the
    seeded demo conflicts keep their well-known identifiers (conf-001, conf-002)
    across re-runs rather than being renumbered.
    """
    cfg = config or DetectionConfig()
    by_id = {w.id: w for w in works}
    pairs = analyse_pairs(works, cfg)
    if not pairs:
        return []

    uf = _UnionFind(by_id.keys())
    for pair in pairs:
        uf.union(pair.work1, pair.work2)

    conflicts: list[Conflict] = []
    counter = 0

    for member_ids in uf.groups().values():
        if len(member_ids) < 2:
            continue

        members = sorted((by_id[i] for i in member_ids), key=lambda w: w.id)
        member_set = {w.id for w in members}
        group_pairs = [
            p for p in pairs if p.work1 in member_set and p.work2 in member_set
        ]

        overlap_type: OverlapType = (
            "both" if any(p.temporalOverlap for p in group_pairs) else "spatial"
        )
        window = _consolidate(members, cfg)
        savings, savings_explanation = _estimate_savings(members, cfg)
        steps = _build_steps(members, group_pairs, window, savings, savings_explanation, cfg)

        key = frozenset(member_set)
        if known_ids and key in known_ids:
            conflict_id = known_ids[key]
        else:
            counter += 1
            conflict_id = f"conf-auto-{counter:03d}"

        primary = members[0]
        location_summary = (
            f"{primary.location.streetName}, Ward {primary.location.ward}"
        )
        severity = _severity(len(members), overlap_type)

        conflicts.append(
            Conflict(
                id=conflict_id,
                workIds=sorted(member_set),
                overlapType=overlap_type,
                proposedWindow=window,
                status="detected",
                reasoningTrace=(
                    f"Detected {len(members)}-way {_OVERLAP_LABEL[overlap_type]} conflict on "
                    f"{location_summary}. Proposed consolidated window "
                    f"{window.start} to {window.end}, sequenced deepest-utility-first."
                ),
                reasoningSteps=steps,
                detectedAt=utcnow_iso(),
                severity=severity,
                savings=savings,
                city=primary.city,
                locationSummary=location_summary,
                traceId=f"trace-{conflict_id}",
            )
        )

    return sorted(conflicts, key=lambda c: c.id)
