"""
Governance surfaces: Agent Identity scope checks and Model Armor screening.

These are honest local stand-ins for the managed Gemini Enterprise Agent
Platform pillars, kept in one module so Phase 4 can swap the implementation for
real Agent Identity / Model Armor calls without touching the routes.

Identity scoping was previously implemented twice — once here and once in the
agent-service — with two different parsers that disagreed on the same input.
This module is now the single implementation; agent-service calls it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal, Optional

# ── Agent Identity ───────────────────────────────────────────────

# agent-identity-<scope>-<nnn>
_IDENTITY_RE = re.compile(r"^agent-identity-(?P<scope>[a-z0-9]+)-(?P<seq>\d+)$")

# Only the Coordinator holds cross-department read scope. That asymmetry is the
# governance design decision called out in PRD §6.2, not an implementation
# detail — every other agent is confined to its own department's collection.
CROSS_DEPARTMENT_SCOPES = {"coordinator"}


@dataclass
class IdentityDecision:
    agent_id: str
    resource: str
    action: str
    result: Literal["GRANTED", "DENIED"]
    reason: str
    scope: str


def parse_scope(agent_id: str) -> Optional[str]:
    match = _IDENTITY_RE.match(agent_id.strip().lower())
    return match.group("scope") if match else None


def resource_scope(resource: str) -> Optional[str]:
    """
    Extract the department scope a resource path belongs to.

    Accepts `departments/dept-water/planned_works/x`, `dept-water/planned_works`
    and bare `dept-water`, which is what callers across the UI actually send.
    """
    parts = [p for p in resource.strip().lower().split("/") if p]
    for part in parts:
        if part.startswith("dept-"):
            return part[len("dept-"):]
    return parts[0] if parts else None


def check_identity(agent_id: str, resource: str, action: str = "read") -> IdentityDecision:
    agent_scope = parse_scope(agent_id)
    target_scope = resource_scope(resource)

    if agent_scope is None:
        return IdentityDecision(
            agent_id, resource, action, "DENIED",
            "Unrecognised agent identity format. Expected agent-identity-<scope>-<nnn>.",
            "none",
        )

    if agent_scope in CROSS_DEPARTMENT_SCOPES:
        return IdentityDecision(
            agent_id, resource, action, "GRANTED",
            "Coordinator identity holds cross-department read scope.",
            "*",
        )

    if action != "read" and target_scope != agent_scope:
        return IdentityDecision(
            agent_id, resource, action, "DENIED",
            f"Write scope is confined to departments/dept-{agent_scope}/**.",
            f"departments/dept-{agent_scope}/**",
        )

    if target_scope and target_scope != agent_scope:
        return IdentityDecision(
            agent_id, resource, action, "DENIED",
            f"Scope violation: the {agent_scope} agent cannot {action} "
            f"{target_scope} resources.",
            f"departments/dept-{agent_scope}/**",
        )

    return IdentityDecision(
        agent_id, resource, action, "GRANTED",
        "Agent scope matches the requested resource.",
        f"departments/dept-{agent_scope}/**",
    )


# ── Model Armor ──────────────────────────────────────────────────

ThreatType = Literal["prompt_injection", "jailbreak", "data_exfiltration"]


@dataclass
class ArmorPattern:
    pattern: re.Pattern
    threat: ThreatType
    label: str


def _p(expr: str, threat: ThreatType, label: str) -> ArmorPattern:
    return ArmorPattern(re.compile(expr, re.IGNORECASE), threat, label)


# Word-boundary anchored so ordinary complaint text does not trip the filter.
# The previous substring list flagged any complaint containing "database",
# "pretend" or "dan" — "Dandekar Road", for instance — which would have been an
# embarrassing false positive to hit live on camera.
ARMOR_PATTERNS: list[ArmorPattern] = [
    _p(r"\bignore\s+(all\s+)?(the\s+)?(previous|prior|above|earlier)\b", "prompt_injection", "instruction override"),
    _p(r"\bdisregard\s+(all\s+)?(the\s+)?(previous|prior|above|your)\b", "prompt_injection", "instruction override"),
    _p(r"\b(system|developer)\s+prompt\b", "prompt_injection", "system prompt probe"),
    _p(r"\bnew\s+instructions?\s*:", "prompt_injection", "injected instruction block"),
    _p(r"</?\s*(system|assistant|instructions?)\s*>", "prompt_injection", "role-tag injection"),
    _p(r"\byou\s+are\s+now\b", "jailbreak", "persona override"),
    _p(r"\bact\s+as\s+(if\s+you\s+are\s+)?(a\s+)?(dan|developer\s+mode|unrestricted)\b", "jailbreak", "persona override"),
    _p(r"\bpretend\s+(that\s+)?you\s+(are|have)\b", "jailbreak", "persona override"),
    _p(r"\bwithout\s+(any\s+)?(restrictions|filters|guardrails)\b", "jailbreak", "guardrail bypass"),
    _p(r"\b(api[_\s-]?key|secret[_\s-]?key|access[_\s-]?token|service[_\s-]?account)\b", "data_exfiltration", "credential probe"),
    _p(r"\b(connection\s+string|firestore\s+credentials?)\b", "data_exfiltration", "credential probe"),
    _p(r"\b(reveal|print|dump|show\s+me)\s+(your|the|all)\s+(prompt|instructions|config|credentials|schema)\b", "data_exfiltration", "configuration probe"),
    _p(r"\blist\s+all\s+(departments|collections|works)\s+(including|regardless)\b", "data_exfiltration", "scope escalation"),
]

_SEVERITY_BY_THREAT: dict[ThreatType, int] = {
    "prompt_injection": 3, "jailbreak": 3, "data_exfiltration": 2,
}


@dataclass
class ArmorVerdict:
    status: Literal["blocked", "passed"]
    severity: Literal["critical", "high", "medium", "none"]
    threats: list[dict] = field(default_factory=list)
    detail: str = ""
    sanitized: str = ""


def scan(text: str) -> ArmorVerdict:
    """Screen untrusted citizen input before it reaches any agent (PRD §10)."""
    detected: list[dict] = []
    for entry in ARMOR_PATTERNS:
        match = entry.pattern.search(text)
        if match:
            detected.append({
                "type": entry.threat,
                "label": entry.label,
                "matched": match.group(0),
                "span": [match.start(), match.end()],
            })

    if not detected:
        return ArmorVerdict(
            status="passed",
            severity="none",
            detail="No threats detected. Input cleared for agent processing.",
            sanitized=text,
        )

    score = sum(_SEVERITY_BY_THREAT[d["type"]] for d in detected)
    severity = "critical" if score >= 5 else "high" if score >= 3 else "medium"

    # Redact rather than discard, so the legitimate part of a complaint is not
    # lost because someone appended an injection to it.
    sanitized = text
    for detection in sorted(detected, key=lambda d: -d["span"][0]):
        start, end = detection["span"]
        sanitized = f"{sanitized[:start]}[REDACTED]{sanitized[end:]}"

    return ArmorVerdict(
        status="blocked",
        severity=severity,
        threats=detected,
        detail=(
            f"Model Armor detected {len(detected)} threat pattern(s) "
            f"({', '.join(sorted({d['type'] for d in detected}))}). "
            f"Input blocked before reaching any agent."
        ),
        sanitized=sanitized,
    )
