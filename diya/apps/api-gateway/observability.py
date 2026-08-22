"""
Agent Observability (PRD §10, tech stack row "Agent Observability / Cloud Trace").

The demo requirement is concrete: pull up a Coordinator decision on camera and
show why it flagged two projects. That needs spans with real timings and a
parent/child structure, not a log line.

This records a span tree per request — id, parent, name, attributes, duration,
status — in a bounded in-process ring buffer, and exports to Cloud Trace when
`OTEL_EXPORT=cloudtrace` and OpenTelemetry are both available. The buffer is the
primary surface either way: Cloud Trace is not reachable in the offline demo,
and an observability story that only works with credentials is not one.

Bounded on purpose. An unbounded trace buffer in a long-running gateway is a
memory leak with a nice name.
"""

from __future__ import annotations

import os
import time
import uuid
from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator, Optional

MAX_TRACES = int(os.environ.get("TRACE_BUFFER", 200))
EXPORT = os.environ.get("OTEL_EXPORT", "").strip().lower()

# The active span, so nested spans attach to their parent without every call
# site having to thread an id through.
_current_span: ContextVar[Optional[str]] = ContextVar("diya_span", default=None)


class Span:
    __slots__ = (
        "id", "traceId", "parentId", "name", "kind",
        "startedAt", "durationMs", "status", "attributes",
    )

    def __init__(
        self, trace_id: str, name: str, kind: str, parent_id: Optional[str]
    ) -> None:
        self.id = uuid.uuid4().hex[:16]
        self.traceId = trace_id
        self.parentId = parent_id
        self.name = name
        self.kind = kind
        self.startedAt = time.time()
        self.durationMs: Optional[float] = None
        self.status = "ok"
        self.attributes: dict[str, Any] = {}

    def set(self, **attributes: Any) -> "Span":
        self.attributes.update(attributes)
        return self

    def dump(self) -> dict:
        return {
            "id": self.id,
            "traceId": self.traceId,
            "parentId": self.parentId,
            "name": self.name,
            "kind": self.kind,
            "startedAt": self.startedAt,
            "durationMs": self.durationMs,
            "status": self.status,
            "attributes": self.attributes,
        }


class Tracer:
    def __init__(self, capacity: int = MAX_TRACES) -> None:
        self._traces: deque[str] = deque(maxlen=capacity)
        self._spans: dict[str, list[Span]] = {}
        self._exporter = _build_exporter()

    @property
    def exporter(self) -> str:
        return self._exporter or "in-memory"

    @contextmanager
    def span(
        self, name: str, kind: str = "internal", trace_id: Optional[str] = None
    ) -> Iterator[Span]:
        parent = _current_span.get()
        if trace_id is None:
            trace_id = self._trace_of(parent) or uuid.uuid4().hex

        span = Span(trace_id, name, kind, parent)
        self._append(span)
        token = _current_span.set(span.id)
        started = time.perf_counter()
        try:
            yield span
        except Exception as exc:  # noqa: BLE001 — recorded, then re-raised
            span.status = "error"
            span.set(error=f"{type(exc).__name__}: {exc}")
            raise
        finally:
            span.durationMs = round((time.perf_counter() - started) * 1000, 2)
            _current_span.reset(token)
            self._export(span)

    # ── storage ──────────────────────────────────────────────────

    def _append(self, span: Span) -> None:
        if span.traceId not in self._spans:
            if len(self._traces) == self._traces.maxlen:
                self._spans.pop(self._traces[0], None)
            self._traces.append(span.traceId)
            self._spans[span.traceId] = []
        self._spans[span.traceId].append(span)

    def _trace_of(self, span_id: Optional[str]) -> Optional[str]:
        if span_id is None:
            return None
        for spans in self._spans.values():
            for span in spans:
                if span.id == span_id:
                    return span.traceId
        return None

    def _export(self, span: Span) -> None:
        if not self._exporter:
            return
        try:
            _export_cloudtrace(span)
        except Exception:  # noqa: BLE001
            # Never let telemetry break the request it is describing.
            self._exporter = None

    # ── read surface ─────────────────────────────────────────────

    def trace(self, trace_id: str) -> Optional[dict]:
        spans = self._spans.get(trace_id)
        if not spans:
            return None
        root = next((s for s in spans if s.parentId is None), spans[0])
        return {
            "traceId": trace_id,
            "root": root.name,
            "startedAt": root.startedAt,
            "durationMs": root.durationMs,
            "status": "error" if any(s.status == "error" for s in spans) else "ok",
            "spanCount": len(spans),
            "spans": [s.dump() for s in spans],
        }

    def recent(self, limit: int = 20) -> list[dict]:
        out = []
        for trace_id in reversed(self._traces):
            summary = self.trace(trace_id)
            if summary:
                out.append({k: v for k, v in summary.items() if k != "spans"})
            if len(out) >= limit:
                break
        return out

    def stats(self) -> dict:
        durations = [
            s.durationMs
            for spans in self._spans.values()
            for s in spans
            if s.durationMs is not None
        ]
        errors = sum(
            1 for spans in self._spans.values() for s in spans if s.status == "error"
        )
        return {
            "exporter": self.exporter,
            "traces": len(self._traces),
            "capacity": self._traces.maxlen,
            "spans": len(durations),
            "errorSpans": errors,
            "p50Ms": _percentile(durations, 0.50),
            "p95Ms": _percentile(durations, 0.95),
        }


def _percentile(values: list[float], q: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(q * len(ordered)))
    return round(ordered[index], 2)


# ── Cloud Trace export (optional) ────────────────────────────────

_cloud_exporter = None


def _build_exporter() -> Optional[str]:
    """Return the exporter name if Cloud Trace export is usable, else None."""
    global _cloud_exporter
    if EXPORT != "cloudtrace":
        return None
    try:
        from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
    except ImportError:
        return None
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    if not project or project == "diya-demo":
        return None
    try:
        _cloud_exporter = CloudTraceSpanExporter(project_id=project)
    except Exception:  # noqa: BLE001
        return None
    return f"cloudtrace:{project}"


def _export_cloudtrace(span: Span) -> None:
    if _cloud_exporter is None:
        return
    _cloud_exporter.export([_to_otel(span)])


def _to_otel(span: Span):  # pragma: no cover — requires the optional dependency
    from opentelemetry.sdk.trace import ReadableSpan

    return ReadableSpan(
        name=span.name,
        attributes={str(k): str(v) for k, v in span.attributes.items()},
    )


tracer = Tracer()
