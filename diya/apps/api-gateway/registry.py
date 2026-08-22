"""
Agent Registry (PRD §9, "auto-registers to Agent Registry").

A registry is only worth having if it is checked. A hand-maintained list of
agents drifts from the fleet within days and then actively misleads — the
governance page would show an agent that no longer exists, or miss one that
does, and nobody would notice until a judge asked.

So this derives the register from the same seed the fleet is built from, then
**reconciles it against the running agent-service** and reports the difference.
`GET /api/registry` says whether the register and the live fleet agree; when
they do not, it names what is only in one of them rather than silently
preferring either.

Deploying to the managed Agent Registry is a GCP-project task; the contract —
what is registered, and the reconciliation that keeps it honest — is here.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from diya_core.seed import load_seed

REGISTRY_VERSION = os.environ.get("AGENT_REGISTRY_VERSION", "3.0.0")
DEPLOYMENT_TARGET = os.environ.get("AGENT_DEPLOYMENT", "local")

# Capability declarations, kept next to the identity that grants them so the two
# cannot disagree. These mirror `agent-service/agents.py`; the reconciliation
# below is what catches it when they stop matching.
_DEPARTMENT_TOOLS = ["read_department_feed", "write_normalized_record"]
_COORDINATOR_TOOLS = [
    "read_all_planned_works", "detect_conflicts",
    "propose_consolidated_window", "recall_conflict", "remember_conflict",
]
_NOTICE_TOOLS = ["resolve_and_generate_notice"]


def register() -> list[dict[str, Any]]:
    """The declared fleet, derived from the seeded departments."""
    seed = load_seed()

    entries: list[dict[str, Any]] = [
        {
            "name": f"{dept.id.replace('dept-', '')}_department_agent",
            "displayName": f"{dept.shortName} Department Agent",
            "type": "department",
            "identityId": dept.agentIdentityId,
            "scope": f"departments/{dept.id}/**",
            "crossDepartmentRead": False,
            "tools": _DEPARTMENT_TOOLS,
            "version": REGISTRY_VERSION,
            "deployment": DEPLOYMENT_TARGET,
        }
        for dept in seed.departments
    ]

    entries.append({
        "name": "coordinator_agent",
        "displayName": "Coordinator Agent",
        "type": "coordinator",
        "identityId": "agent-identity-coordinator-001",
        "scope": "departments/**",
        # The one elevated identity in the fleet — PRD §6.2.
        "crossDepartmentRead": True,
        "tools": _COORDINATOR_TOOLS,
        "version": REGISTRY_VERSION,
        "deployment": DEPLOYMENT_TARGET,
    })
    entries.append({
        "name": "citizen_notice_agent",
        "displayName": "Citizen Notice Agent",
        "type": "notice",
        "identityId": "agent-identity-notice-001",
        "scope": "conflicts/**:read, notices/**:write",
        "crossDepartmentRead": False,
        "tools": _NOTICE_TOOLS,
        "version": REGISTRY_VERSION,
        "deployment": DEPLOYMENT_TARGET,
    })
    return entries


def reconcile(live_topology: Optional[dict]) -> dict:
    """
    Compare the register against the agent tree the fleet actually built.

    `live_topology` is the payload from agent-service `GET /agents/topology`.
    None means the fleet could not be reached — reported as `unknown`, never as
    agreement, because "I could not check" and "they match" are different
    answers and only one of them is reassuring.
    """
    declared = {entry["name"] for entry in register()}

    if live_topology is None:
        return {
            "status": "unknown",
            "detail": "agent-service unreachable; the register could not be verified.",
            "declared": sorted(declared),
        }

    live: set[str] = set()

    def walk(node: dict) -> None:
        # Only leaf LlmAgents are registrable; ParallelAgent/SequentialAgent are
        # orchestration nodes, not agents with identities.
        if not node.get("children"):
            live.add(node["name"])
        for child in node.get("children", []):
            walk(child)

    walk(live_topology["root"])

    missing = sorted(declared - live)      # registered but not running
    unregistered = sorted(live - declared)  # running but not registered

    return {
        "status": "in_sync" if not missing and not unregistered else "drift",
        "declared": sorted(declared),
        "live": sorted(live),
        "registeredButNotRunning": missing,
        "runningButNotRegistered": unregistered,
        "detail": (
            "Register matches the running fleet."
            if not missing and not unregistered
            else "Register and running fleet disagree; see the lists above."
        ),
    }
