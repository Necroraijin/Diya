"""
Persistence.

Two implementations behind one async interface:

* MemoryRepository   — seeds from data/synthetic, holds state in-process.
                       Default, and what `docker compose up` uses out of the box.
* FirestoreRepository — the real Firestore collections described in PRD §7.
                       Selected with DIYA_STORE=firestore.

Firestore is optional at import time: the google-cloud-firestore import lives
inside the class so services that never touch it do not need the dependency
installed. Set FIRESTORE_EMULATOR_HOST to run it locally without a GCP project.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Optional

from diya_core.conflict import DetectionConfig, detect_conflicts
from diya_core.models import (
    AgentActivity,
    Conflict,
    Department,
    Notice,
    PlannedWork,
    utcnow_iso,
)
from diya_core.seed import load_seed

# Firestore collection names — PRD §7.
COL_DEPARTMENTS = "departments"
COL_PLANNED_WORKS = "planned_works"
COL_CONFLICTS = "conflicts"
COL_NOTICES = "notices"
COL_ACTIVITIES = "agent_activities"


class Repository(ABC):
    """Storage interface used by every service."""

    @abstractmethod
    async def init(self) -> None: ...

    @abstractmethod
    async def list_departments(self) -> list[Department]: ...

    @abstractmethod
    async def list_works(
        self, dept_id: Optional[str] = None, city: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[PlannedWork]: ...

    @abstractmethod
    async def get_work(self, work_id: str) -> Optional[PlannedWork]: ...

    @abstractmethod
    async def upsert_work(self, work: PlannedWork) -> PlannedWork: ...

    @abstractmethod
    async def list_conflicts(
        self, status: Optional[str] = None, city: Optional[str] = None
    ) -> list[Conflict]: ...

    @abstractmethod
    async def get_conflict(self, conflict_id: str) -> Optional[Conflict]: ...

    @abstractmethod
    async def upsert_conflict(self, conflict: Conflict) -> Conflict: ...

    @abstractmethod
    async def list_notices(self) -> list[Notice]: ...

    @abstractmethod
    async def get_notice(self, notice_id: str) -> Optional[Notice]: ...

    @abstractmethod
    async def upsert_notice(self, notice: Notice) -> Notice: ...

    @abstractmethod
    async def list_activities(
        self, agent_type: Optional[str] = None, limit: int = 20
    ) -> list[AgentActivity]: ...

    @abstractmethod
    async def add_activity(self, activity: AgentActivity) -> AgentActivity: ...

    # ── Shared behaviour ────────────────────────────────────────────

    async def run_detection(
        self, config: Optional[DetectionConfig] = None
    ) -> list[Conflict]:
        """
        Re-run detection over all stored works and persist the results.

        Conflicts already marked resolved or dismissed keep that status — this is
        the durable equivalent of the Memory Bank behaviour in PRD §6.2, so a
        re-run does not re-flag something a coordinator already signed off.
        """
        works = await self.list_works()
        seed = load_seed()
        detected = detect_conflicts(works, config, seed.known_conflict_ids)

        existing = {c.id: c for c in await self.list_conflicts()}
        saved: list[Conflict] = []

        for conflict in detected:
            prior = existing.get(conflict.id)
            if prior and prior.status in ("resolved", "dismissed"):
                conflict.status = prior.status
                conflict.resolvedAt = prior.resolvedAt
                conflict.detectedAt = prior.detectedAt
            saved.append(await self.upsert_conflict(conflict))

        conflicted_ids = {wid for c in saved for wid in c.workIds}
        for work in works:
            desired = "conflicted" if work.id in conflicted_ids else "planned"
            if work.status != desired:
                work.status = desired
                await self.upsert_work(work)

        return saved


class MemoryRepository(Repository):
    """In-process store seeded from data/synthetic. State resets on restart."""

    def __init__(self) -> None:
        self._departments: list[Department] = []
        self._works: dict[str, PlannedWork] = {}
        self._conflicts: dict[str, Conflict] = {}
        self._notices: dict[str, Notice] = {}
        self._activities: list[AgentActivity] = []
        self._ready = False

    async def init(self) -> None:
        if self._ready:
            return
        seed = load_seed()
        self._departments = list(seed.departments)
        self._works = {w.id: w for w in seed.works}
        self._ready = True
        await self.run_detection()

    async def list_departments(self) -> list[Department]:
        return list(self._departments)

    async def list_works(self, dept_id=None, city=None, status=None) -> list[PlannedWork]:
        works = list(self._works.values())
        if dept_id:
            works = [w for w in works if w.deptId == dept_id]
        if city:
            works = [w for w in works if w.city == city]
        if status:
            works = [w for w in works if w.status == status]
        return works

    async def get_work(self, work_id: str) -> Optional[PlannedWork]:
        return self._works.get(work_id)

    async def upsert_work(self, work: PlannedWork) -> PlannedWork:
        self._works[work.id] = work
        return work

    async def list_conflicts(self, status=None, city=None) -> list[Conflict]:
        conflicts = list(self._conflicts.values())
        if status:
            conflicts = [c for c in conflicts if c.status == status]
        if city:
            conflicts = [c for c in conflicts if c.city == city]
        return sorted(conflicts, key=lambda c: c.id)

    async def get_conflict(self, conflict_id: str) -> Optional[Conflict]:
        return self._conflicts.get(conflict_id)

    async def upsert_conflict(self, conflict: Conflict) -> Conflict:
        self._conflicts[conflict.id] = conflict
        return conflict

    async def list_notices(self) -> list[Notice]:
        return sorted(self._notices.values(), key=lambda n: n.generatedAt, reverse=True)

    async def get_notice(self, notice_id: str) -> Optional[Notice]:
        return self._notices.get(notice_id)

    async def upsert_notice(self, notice: Notice) -> Notice:
        self._notices[notice.id] = notice
        return notice

    async def list_activities(self, agent_type=None, limit=20) -> list[AgentActivity]:
        items = self._activities
        if agent_type:
            items = [a for a in items if a.agentType == agent_type]
        return sorted(items, key=lambda a: a.timestamp, reverse=True)[:limit]

    async def add_activity(self, activity: AgentActivity) -> AgentActivity:
        self._activities.append(activity)
        del self._activities[:-500]
        return activity


class FirestoreRepository(Repository):
    """Firestore-backed store using the async client."""

    def __init__(self, project: Optional[str] = None) -> None:
        from google.cloud import firestore  # imported lazily — optional dependency

        self._db = firestore.AsyncClient(
            project=project or os.environ.get("GOOGLE_CLOUD_PROJECT")
        )
        self._ready = False

    async def init(self) -> None:
        """Seed Firestore on first run if the works collection is empty."""
        if self._ready:
            return
        existing = [d async for d in self._db.collection(COL_PLANNED_WORKS).limit(1).stream()]
        if not existing:
            seed = load_seed()
            for dept in seed.departments:
                await self._db.collection(COL_DEPARTMENTS).document(dept.id).set(
                    dept.model_dump()
                )
            for work in seed.works:
                await self._db.collection(COL_PLANNED_WORKS).document(work.id).set(
                    work.model_dump()
                )
        self._ready = True
        await self.run_detection()

    async def _all(self, collection: str, model):
        return [model(**doc.to_dict()) async for doc in self._db.collection(collection).stream()]

    async def _one(self, collection: str, doc_id: str, model):
        snap = await self._db.collection(collection).document(doc_id).get()
        return model(**snap.to_dict()) if snap.exists else None

    async def list_departments(self) -> list[Department]:
        return await self._all(COL_DEPARTMENTS, Department)

    async def list_works(self, dept_id=None, city=None, status=None) -> list[PlannedWork]:
        query = self._db.collection(COL_PLANNED_WORKS)
        if dept_id:
            query = query.where("deptId", "==", dept_id)
        if city:
            query = query.where("city", "==", city)
        if status:
            query = query.where("status", "==", status)
        return [PlannedWork(**doc.to_dict()) async for doc in query.stream()]

    async def get_work(self, work_id: str) -> Optional[PlannedWork]:
        return await self._one(COL_PLANNED_WORKS, work_id, PlannedWork)

    async def upsert_work(self, work: PlannedWork) -> PlannedWork:
        await self._db.collection(COL_PLANNED_WORKS).document(work.id).set(work.model_dump())
        return work

    async def list_conflicts(self, status=None, city=None) -> list[Conflict]:
        query = self._db.collection(COL_CONFLICTS)
        if status:
            query = query.where("status", "==", status)
        if city:
            query = query.where("city", "==", city)
        items = [Conflict(**doc.to_dict()) async for doc in query.stream()]
        return sorted(items, key=lambda c: c.id)

    async def get_conflict(self, conflict_id: str) -> Optional[Conflict]:
        return await self._one(COL_CONFLICTS, conflict_id, Conflict)

    async def upsert_conflict(self, conflict: Conflict) -> Conflict:
        await self._db.collection(COL_CONFLICTS).document(conflict.id).set(
            conflict.model_dump()
        )
        return conflict

    async def list_notices(self) -> list[Notice]:
        items = await self._all(COL_NOTICES, Notice)
        return sorted(items, key=lambda n: n.generatedAt, reverse=True)

    async def get_notice(self, notice_id: str) -> Optional[Notice]:
        return await self._one(COL_NOTICES, notice_id, Notice)

    async def upsert_notice(self, notice: Notice) -> Notice:
        await self._db.collection(COL_NOTICES).document(notice.id).set(notice.model_dump())
        return notice

    async def list_activities(self, agent_type=None, limit=20) -> list[AgentActivity]:
        query = self._db.collection(COL_ACTIVITIES)
        if agent_type:
            query = query.where("agentType", "==", agent_type)
        items = [AgentActivity(**doc.to_dict()) async for doc in query.stream()]
        return sorted(items, key=lambda a: a.timestamp, reverse=True)[:limit]

    async def add_activity(self, activity: AgentActivity) -> AgentActivity:
        await self._db.collection(COL_ACTIVITIES).document(activity.id).set(
            activity.model_dump()
        )
        return activity


_repository: Optional[Repository] = None


def get_repository() -> Repository:
    """
    Process-wide repository singleton.

    DIYA_STORE=firestore selects Firestore; anything else (or unset) uses memory.
    If Firestore is selected but unavailable, this falls back to memory with a
    warning rather than failing startup — a demo should never die on a missing
    credential.
    """
    global _repository
    if _repository is not None:
        return _repository

    if os.environ.get("DIYA_STORE", "memory").lower() == "firestore":
        try:
            _repository = FirestoreRepository()
            return _repository
        except Exception as exc:  # noqa: BLE001 — deliberate degrade-to-memory
            print(f"[diya_core] Firestore unavailable ({exc}); using in-memory store.")

    _repository = MemoryRepository()
    return _repository
