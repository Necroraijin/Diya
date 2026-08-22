"""
Pipeline execution.

Two runners, one tool set:

  * `run_adk` drives the real ADK agent tree through a `Runner`. It needs a
    reachable Gemini backend.
  * `run_deterministic` calls the same tools in the same order without a model.

The deterministic runner is not a stub standing in for missing work — it is the
execution path the demo runs on, and the one that makes the pipeline verifiable.
Every number it reports came from `diya_core.conflict`, so the two runners
produce the same conflicts, the same phase ordering and the same savings. What
the LLM path adds is narration, not arithmetic.

Both paths share the max-turn cap from PRD red flag #9: the Coordinator is the
component most likely to loop, so the ceiling is enforced by the runner rather
than trusted to the model's own instruction.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import tools as t
from memory import memory_bank

MAX_TURNS = int(os.environ.get("AGENT_MAX_TURNS", 10))

# The cap exists for the Coordinator's negotiation loop (PRD red flag #9) — the
# component that can actually run away. Department ingestion is bounded by the
# number of departments, so counting it against the same budget only starved
# the stage the cap was written to protect.
CAPPED_AGENTS = {"coordinator", "citizen_notice"}


@dataclass
class Step:
    agent: str
    tool: str
    status: str          # ok | denied | error | skipped
    detail: str
    durationMs: int
    result: Any = None


@dataclass
class RunResult:
    mode: str
    steps: list[Step] = field(default_factory=list)
    conflicts: list[dict] = field(default_factory=list)
    notices: list[dict] = field(default_factory=list)
    turns: int = 0
    truncated: bool = False
    error: Optional[str] = None

    def dump(self) -> dict:
        return {
            "mode": self.mode,
            "steps": [s.__dict__ for s in self.steps],
            "conflicts": self.conflicts,
            "notices": self.notices,
            "turns": self.turns,
            "maxTurns": MAX_TURNS,
            "truncated": self.truncated,
            "error": self.error,
        }


class _Tracker:
    """Records each tool call and enforces the turn ceiling."""

    def __init__(self, result: RunResult) -> None:
        self.result = result

    @property
    def exhausted(self) -> bool:
        return self.result.turns >= MAX_TURNS

    async def call(self, agent: str, tool: str, coro_factory, detail: str = "") -> Any:
        capped = agent in CAPPED_AGENTS
        if capped and self.exhausted:
            self.result.truncated = True
            self.result.steps.append(
                Step(agent, tool, "skipped", f"Turn cap of {MAX_TURNS} reached.", 0)
            )
            return None

        if capped:
            self.result.turns += 1
        started = time.perf_counter()
        try:
            value = await coro_factory()
        except t.ScopeDenied as denied:
            self.result.steps.append(
                Step(
                    agent, tool, "denied", denied.reason,
                    int((time.perf_counter() - started) * 1000),
                )
            )
            return None
        except t.GatewayError as exc:
            self.result.steps.append(
                Step(
                    agent, tool, "error", str(exc),
                    int((time.perf_counter() - started) * 1000),
                )
            )
            return None

        self.result.steps.append(
            Step(
                agent, tool, "ok", detail or _summarise(value),
                int((time.perf_counter() - started) * 1000),
                result=value,
            )
        )
        return value


def _summarise(value: Any) -> str:
    if isinstance(value, dict):
        # Order matters: the detect payload carries both keys.
        if "conflicts" in value:
            return f"{len(value['conflicts'])} conflict(s)."
        if "count" in value:
            return f"{value['count']} record(s)."
        if "notice" in value:
            return "Notice artifacts generated."
    return "OK."


# ── Deterministic runner ─────────────────────────────────────────

async def run_deterministic(
    departments: list[dict[str, Any]],
    *,
    auto_resolve: bool = False,
) -> RunResult:
    """
    Execute the full pipeline without a model.

    `auto_resolve` drives the Notice Agent leg. It is off by default because
    resolution is a human decision in this design — the Coordinator proposes,
    a coordinator signs off, and only then does the notice go out.
    """
    result = RunResult(mode="deterministic")
    track = _Tracker(result)

    # ── Stage 1: department agents (independent, PRD §6.1) ──
    for dept in departments:
        dept_id = dept["id"]
        identity = dept["agentIdentityId"]
        agent = f"{dept_id} agent"

        feed = await track.call(
            agent, "read_department_feed",
            lambda d=dept_id, i=identity: t.read_department_feed(d, i),
        )
        if feed is None:
            continue
        await track.call(
            agent, "write_normalized_record",
            lambda d=dept_id, i=identity: t.write_normalized_record(d, i),
            detail=f"Published {feed['count']} normalised record(s).",
        )

    # ── Stage 2: coordinator (PRD §6.2) ──
    await track.call(
        "coordinator", "read_all_planned_works",
        t.read_all_planned_works,
        detail="Cross-department read — the one elevated Identity in the fleet.",
    )
    detected = await track.call("coordinator", "detect_conflicts", t.detect_conflicts)

    conflicts = (detected or {}).get("conflicts", [])
    for conflict in conflicts:
        conflict_id = conflict["id"]

        # Memory Bank check before surfacing anything (PRD §6.2).
        prior = memory_bank.recall(conflict_id)
        if prior:
            result.steps.append(
                Step(
                    "coordinator", "recall_conflict", "ok",
                    f"Seen before: first surfaced {prior['firstSeen']}, "
                    f"{prior['timesSurfaced']} time(s), last outcome "
                    f"'{prior['outcome']}'.",
                    0, result=prior,
                )
            )
        else:
            result.steps.append(
                Step("coordinator", "recall_conflict", "ok", "Not seen before.", 0)
            )

        if conflict["status"] in ("resolved", "dismissed"):
            result.steps.append(
                Step(
                    "coordinator", "propose_consolidated_window", "skipped",
                    f"{conflict_id} is already {conflict['status']}; not re-flagged.",
                    0,
                )
            )
        else:
            window = await track.call(
                "coordinator", "propose_consolidated_window",
                lambda c=conflict_id: t.propose_consolidated_window(c),
                detail=(
                    f"{conflict_id}: {len(conflict.get('workIds', []))} works into one "
                    f"window with {len((conflict.get('proposedWindow') or {}).get('phases', []))} "
                    f"phases."
                ),
            )
            if window is None:
                continue

        memory_bank.remember(
            conflict_id,
            outcome=conflict["status"],
            work_ids=conflict.get("workIds", []),
            detail=conflict.get("description", ""),
        )

    result.conflicts = conflicts

    # ── Stage 3: notice agent, conditional on resolution (PRD §6.4) ──
    for conflict in conflicts:
        if conflict["status"] == "resolved":
            # Already resolved in an earlier run; its artifacts exist.
            continue
        if not auto_resolve:
            result.steps.append(
                Step(
                    "citizen_notice", "resolve_and_generate_notice", "skipped",
                    f"{conflict['id']} awaits human sign-off before a notice is issued.",
                    0,
                )
            )
            continue

        notice = await track.call(
            "citizen_notice", "resolve_and_generate_notice",
            lambda c=conflict["id"]: t.resolve_and_generate_notice(c),
            detail=f"Notice artifacts generated for {conflict['id']}.",
        )
        if notice:
            result.notices.append(notice)
            memory_bank.remember(
                conflict["id"],
                outcome="resolved",
                work_ids=conflict.get("workIds", []),
                detail="Notice issued.",
            )

    return result


def _describe_exception(exc: BaseException, depth: int = 0) -> str:
    """Flatten an ExceptionGroup down to its distinct underlying causes."""
    inner = getattr(exc, "exceptions", None)
    if inner and depth < 3:
        causes = {_describe_exception(e, depth + 1) for e in inner}
        return "; ".join(sorted(causes))
    return f"{type(exc).__name__}: {exc}"


# ── ADK runner ───────────────────────────────────────────────────

async def run_adk(departments: list[dict[str, Any]], prompt: str) -> RunResult:
    """Drive the real ADK tree. Requires a reachable Gemini backend."""
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    import agents as fleet

    root = fleet.build_fleet(departments)
    if root is None:
        return RunResult(mode="adk", error="google-adk is not installed.")

    result = RunResult(mode="adk")
    runner = InMemoryRunner(agent=root, app_name="diya")
    session = await runner.session_service.create_session(
        app_name="diya", user_id="coordinator"
    )

    try:
        async for event in runner.run_async(
            user_id="coordinator",
            session_id=session.id,
            new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
        ):
            for part in (event.content.parts if event.content else []) or []:
                if getattr(part, "function_call", None):
                    result.turns += 1
                    result.steps.append(
                        Step(
                            event.author, part.function_call.name, "ok",
                            f"args={dict(part.function_call.args or {})}", 0,
                        )
                    )
                elif getattr(part, "text", None):
                    result.steps.append(
                        Step(event.author, "reply", "ok", part.text.strip(), 0)
                    )
            if result.turns >= MAX_TURNS:
                result.truncated = True
                break
    except Exception as exc:  # noqa: BLE001 — surfaced to the caller
        # ADK runs sub-agents in a TaskGroup, so a missing credential arrives as
        # an ExceptionGroup whose repr says only "4 sub-exceptions". Unwrap it —
        # the person reading this needs the cause, not the wrapper.
        result.error = _describe_exception(exc)
    finally:
        await runner.close()

    return result
