"""
diya_core — shared domain layer for all DIYA Python services.

This package is the single source of truth for the data model, the seed
dataset, the conflict-detection algorithm and persistence. Services import
from here rather than defining their own copies of departments/works/conflicts.
"""

from diya_core.models import (
    AgentActivity,
    Conflict,
    Department,
    Location,
    Notice,
    PlannedWork,
    ProposedWindow,
    ReasoningStep,
    WindowPhase,
)
from diya_core.conflict import detect_conflicts, DetectionConfig
from diya_core.repository import Repository, get_repository
from diya_core.events import EventBus, event_bus
from diya_core.seed import load_seed

__all__ = [
    "AgentActivity",
    "Conflict",
    "Department",
    "DetectionConfig",
    "EventBus",
    "Location",
    "Notice",
    "PlannedWork",
    "ProposedWindow",
    "ReasoningStep",
    "Repository",
    "WindowPhase",
    "detect_conflicts",
    "event_bus",
    "get_repository",
    "load_seed",
]
