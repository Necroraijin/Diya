"""
ADK agent fleet and orchestration (PRD §6.4).

Shape, as specified:

    ParallelAgent(department agents)  ->  Coordinator  ->  Citizen Notice Agent

The Department Agents are independent — nothing one reads affects another — so
they run in parallel; the Coordinator cannot start until all feeds are in, so
that edge is sequential.

Two things are deliberate here.

**The tools are the ones in `tools.py`.** Each agent is handed only the tools
its Identity can actually use. A Department Agent has no tool that reads another
department, so the scope boundary is enforced twice: once by the tool's own
gateway-side Identity check, and once by simply not being reachable from that
agent. Defence in depth is cheap when it is this structural.

**The Coordinator does not do the arithmetic.** Overlap distances, phase
ordering and rupee savings come from `diya_core.conflict` through the
`detect_conflicts` tool. The model's job is to sequence tools, apply the
memory check, and explain the result — not to invent numbers a judge might
verify. This is why the instructions below forbid it explicitly.

Building this tree does not require credentials; running it does. When Vertex
is unreachable, `orchestrator.py` executes the identical tool sequence
deterministically, and the service reports which path ran.
"""

from __future__ import annotations

import os
from typing import Any, Optional

MODEL = os.environ.get("AGENT_MODEL", "gemini-flash-latest")
MAX_TURNS = int(os.environ.get("AGENT_MAX_TURNS", 10))

COORDINATOR_IDENTITY = "agent-identity-coordinator-001"
NOTICE_IDENTITY = "agent-identity-notice-001"


def adk_available() -> tuple[bool, str]:
    """Whether the ADK package can be imported, and why not if it cannot."""
    try:
        import google.adk  # noqa: F401
    except ImportError as exc:
        return False, f"google-adk not installed ({exc})"
    return True, ""


def vertex_configured() -> tuple[bool, str]:
    """
    Whether an LLM backend is actually reachable.

    ADK talks to Gemini either through Vertex (project + location) or through
    an API key. Neither present means the LlmAgents would fail on their first
    turn, so the service runs the deterministic path instead of emitting a
    trace full of errors.
    """
    if os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"):
        return True, ""
    use_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in {"1", "true"}
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    if use_vertex and project and project != "diya-demo":
        return True, ""
    return False, (
        "No LLM backend configured. Set GOOGLE_API_KEY, or "
        "GOOGLE_GENAI_USE_VERTEXAI=true with a real GOOGLE_CLOUD_PROJECT."
    )


# ── Instructions ─────────────────────────────────────────────────

_DEPT_INSTRUCTION = """\
You are the {name} planning agent for {dept_name}.

Your only job is to bring your own department's planned works into the shared
schema and hand them to the ingestion pipeline.

Steps, in order:
1. Call `read_department_feed` for department `{dept_id}`.
2. Call `write_normalized_record` for the same department.
3. Report how many records you published, in one sentence.

You may only touch department `{dept_id}`. If you are ever asked to read
another department's records, refuse and say why — the Coordinator is the only
identity with cross-department read scope. Do not invent records, dates or
budgets; report exactly what the tools return.
"""

_COORDINATOR_INSTRUCTION = """\
You are the Coordinator Agent for a municipal dig-once programme.

You hold the only Agent Identity with cross-department read scope. Use it
carefully and say so when you exercise it.

Steps, in order:
1. Call `read_all_planned_works` to see every department's records.
2. Call `detect_conflicts` to run the deterministic detector.
3. For each conflict returned, call `recall_conflict` first. If it has been
   seen before, say when and do not present it as new. If it was already
   resolved or dismissed, leave it alone.
4. For each genuinely new conflict, call `propose_consolidated_window` and
   summarise the phase order and the reason for it.
5. Call `remember_conflict` for every conflict you surfaced.

Hard rules:
- Never compute or estimate overlap distances, dates or savings yourself.
  Those come from the tools. If a tool did not give you a number, say you do
  not have it rather than producing one.
- Stop after at most {max_turns} tool turns and report what you have. Looping
  between departments is the failure mode this cap exists to prevent.
- You propose. You never mark a conflict resolved — a human coordinator does
  that, and only then does the Notice Agent run.
"""

_NOTICE_INSTRUCTION = """\
You are the Citizen Notice Agent.

When a conflict has been resolved, call `resolve_and_generate_notice` for it and
report the returned PDF and ICS URLs.

The output is read by the public, so keep the language plain and factual. Never
claim a closure date, department or saving that is not in the tool result. The
underlying dataset is synthetic demonstration data and the generated notice says
so — do not remove or contradict that.
"""


# ── Fleet construction ───────────────────────────────────────────

def build_fleet(departments: list[dict[str, Any]]) -> Optional[Any]:
    """
    Build the ADK agent tree, or return None if ADK is not installed.

    `departments` is the seeded department list; one Department Agent is
    created per entry, each closed over its own id and identity.
    """
    ok, _ = adk_available()
    if not ok:
        return None

    from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
    from google.adk.tools import FunctionTool

    import tools as t
    from memory import memory_bank

    # ── Per-department agents, each with only its own tools ──
    dept_agents = []
    for dept in departments:
        dept_id = dept["id"]
        identity = dept["agentIdentityId"]
        short = dept_id.replace("dept-", "")

        async def read_feed(dept_id: str = dept_id, agent_id: str = identity) -> dict:
            """Read this department's planned works."""
            return await t.read_department_feed(dept_id, agent_id)

        async def write_records(dept_id: str = dept_id, agent_id: str = identity) -> dict:
            """Publish this department's normalised records to the ingestion topic."""
            return await t.write_normalized_record(dept_id, agent_id)

        dept_agents.append(
            LlmAgent(
                name=f"{short}_department_agent",
                model=MODEL,
                description=f"Normalises planned works for {dept['name']}.",
                instruction=_DEPT_INSTRUCTION.format(
                    name=short.title(),
                    dept_name=dept["name"],
                    dept_id=dept_id,
                ),
                tools=[FunctionTool(read_feed), FunctionTool(write_records)],
                # A department agent must never hand control to a peer; that is
                # exactly the cross-department path the Identity model forbids.
                disallow_transfer_to_peers=True,
                output_key=f"feed_{short}",
            )
        )

    ingestion = ParallelAgent(
        name="department_ingestion",
        description="All department agents normalise their feeds concurrently.",
        sub_agents=dept_agents,
    )

    # ── Coordinator, the only cross-department reader ──
    def recall_conflict(conflict_id: str) -> dict:
        """Check whether this conflict has been surfaced in an earlier session."""
        entry = memory_bank.recall(conflict_id)
        return entry or {"conflictId": conflict_id, "seenBefore": False}

    def remember_conflict(conflict_id: str, outcome: str, detail: str = "") -> dict:
        """Record that this conflict was surfaced, for future sessions."""
        return memory_bank.remember(
            conflict_id, outcome=outcome, work_ids=[], detail=detail
        )

    coordinator = LlmAgent(
        name="coordinator_agent",
        model=MODEL,
        description="Detects cross-department conflicts and proposes consolidated windows.",
        instruction=_COORDINATOR_INSTRUCTION.format(max_turns=MAX_TURNS),
        tools=[
            FunctionTool(t.read_all_planned_works),
            FunctionTool(t.detect_conflicts),
            FunctionTool(t.propose_consolidated_window),
            FunctionTool(recall_conflict),
            FunctionTool(remember_conflict),
        ],
        output_key="coordinator_findings",
    )

    notice = LlmAgent(
        name="citizen_notice_agent",
        model=MODEL,
        description="Generates the public works notice PDF and closure calendar.",
        instruction=_NOTICE_INSTRUCTION,
        tools=[FunctionTool(t.resolve_and_generate_notice)],
        output_key="notice_result",
    )

    return SequentialAgent(
        name="diya_pipeline",
        description="Department ingestion -> conflict coordination -> citizen notice.",
        sub_agents=[ingestion, coordinator, notice],
    )


def describe_fleet(root: Any) -> dict:
    """Flatten the agent tree for the architecture view."""

    def node(agent: Any) -> dict:
        return {
            "name": agent.name,
            "type": type(agent).__name__,
            "description": getattr(agent, "description", ""),
            "model": getattr(agent, "model", None) or None,
            "tools": [
                getattr(tool, "name", type(tool).__name__)
                for tool in getattr(agent, "tools", [])
            ],
            "children": [node(child) for child in getattr(agent, "sub_agents", [])],
        }

    return node(root)
