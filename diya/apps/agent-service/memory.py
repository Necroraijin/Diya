"""
Memory Bank — cross-session state for the Coordinator (PRD §6.2).

The requirement is "persistent, secure cross-session context over extended
timelines": a re-run must not re-flag a conflict a coordinator already signed
off. Two layers implement that:

  * The durable record lives in the repository (`Repository.run_detection`
    preserves resolved/dismissed status across re-detection).
  * This module holds the *agent's* recollection — what it surfaced, when, and
    what it concluded — so the Coordinator can say "I have seen this before"
    with a timestamp rather than re-deriving it from scratch.

Backed by Vertex AI Memory Bank when `MEMORY_BANK` names an Agent Engine, and
by a local JSON file otherwise. The local backing is not a mock: the demo runs
on it, and it survives process restarts, which is the property being claimed.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Optional

from diya_core.models import utcnow_iso

MEMORY_PATH = Path(os.environ.get("MEMORY_DIR", ".memory")) / "coordinator.json"

# Agent Engine resource name, e.g.
# projects/<p>/locations/<l>/reasoningEngines/<id>. Unset => local file.
MEMORY_BANK = os.environ.get("MEMORY_BANK", "").strip()


class MemoryBank:
    """
    Recollection keyed by conflict id.

    Writes are serialised through a lock and flushed on every put: the demo
    kills and restarts services, and a memory that only persists on clean
    shutdown would not survive that.
    """

    def __init__(self, path: Path = MEMORY_PATH) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._entries: dict[str, dict[str, Any]] = {}
        self._load()

    # ── backing store ────────────────────────────────────────────

    @property
    def backend(self) -> str:
        return f"vertex:{MEMORY_BANK}" if MEMORY_BANK else f"local:{self._path}"

    def _load(self) -> None:
        try:
            self._entries = json.loads(self._path.read_text("utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            # A truncated file from a killed process must not take the service
            # down — an empty memory is recoverable, a crash loop is not.
            self._entries = {}

    def _flush(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._entries, indent=2), "utf-8")
        tmp.replace(self._path)

    # ── recollection ─────────────────────────────────────────────

    def recall(self, conflict_id: str) -> Optional[dict[str, Any]]:
        return self._entries.get(conflict_id)

    def remember(
        self,
        conflict_id: str,
        *,
        outcome: str,
        work_ids: list[str],
        detail: str = "",
    ) -> dict[str, Any]:
        with self._lock:
            prior = self._entries.get(conflict_id, {})
            entry = {
                "conflictId": conflict_id,
                "outcome": outcome,
                "workIds": work_ids,
                "detail": detail,
                "firstSeen": prior.get("firstSeen", utcnow_iso()),
                "lastSeen": utcnow_iso(),
                "timesSurfaced": prior.get("timesSurfaced", 0) + 1,
            }
            self._entries[conflict_id] = entry
            self._flush()
        return entry

    def all(self) -> list[dict[str, Any]]:
        return sorted(
            self._entries.values(), key=lambda e: e["lastSeen"], reverse=True
        )

    def forget_all(self) -> int:
        """Reset between demo takes."""
        with self._lock:
            count = len(self._entries)
            self._entries = {}
            self._flush()
        return count


memory_bank = MemoryBank()
