"""
Agent Gateway policy enforcement (PRD §10, tech stack row "Agent Gateway").

Phase 2 published these numbers on `/api/governance/stats` — rate limit, timeout,
circuit-breaker threshold — but nothing enforced them. Reporting a policy you do
not apply is worse than having no policy: it invites exactly the question "so
what happens at 101 requests?" with no answer. This module answers it.

Three controls, all applied to real traffic:

  * **Rate limiting**, per calling identity. A token bucket, so a burst is
    allowed but a sustained flood is not — agents legitimately fan out.
  * **Circuit breaker**, per upstream. After N consecutive failures the gateway
    stops dialling a dead service and fails fast, then probes once the cooldown
    passes. Without this, one down service turns every request into a 30-second
    hang.
  * **Timeouts**, per call, so a hung upstream cannot pin a worker forever.

All state is per-process and in-memory. That is honest for a single-replica
gateway; a multi-replica deployment would need shared counters, and the limits
would then be per-replica rather than global — noted here because the difference
matters if anyone deploys this behind a load balancer.
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Literal, Optional

RATE_LIMIT_PER_MIN = int(os.environ.get("AGENT_RATE_LIMIT", 100))
CIRCUIT_BREAKER_THRESHOLD = int(os.environ.get("AGENT_CIRCUIT_BREAKER", 5))
CIRCUIT_BREAKER_COOLDOWN = float(os.environ.get("AGENT_CIRCUIT_COOLDOWN", 30))
TIMEOUT_SECONDS = float(os.environ.get("AGENT_TIMEOUT_SECONDS", 30))


# ── Rate limiting ────────────────────────────────────────────────

@dataclass
class _Bucket:
    tokens: float
    updated: float


class RateLimiter:
    """
    Token bucket keyed by caller identity.

    Capacity equals the per-minute allowance, refilled continuously, so a caller
    may burst up to the full allowance and then proceeds at the sustained rate.
    """

    def __init__(self, per_minute: int = RATE_LIMIT_PER_MIN) -> None:
        self.per_minute = per_minute
        self._rate = per_minute / 60.0
        self._buckets: dict[str, _Bucket] = {}
        self._lock = asyncio.Lock()
        self.rejections = 0

    async def check(self, caller: str) -> tuple[bool, float]:
        """Consume one token. Returns (allowed, retry_after_seconds)."""
        now = time.monotonic()
        async with self._lock:
            bucket = self._buckets.get(caller)
            if bucket is None:
                self._buckets[caller] = _Bucket(self.per_minute - 1, now)
                return True, 0.0

            bucket.tokens = min(
                float(self.per_minute),
                bucket.tokens + (now - bucket.updated) * self._rate,
            )
            bucket.updated = now

            if bucket.tokens < 1:
                self.rejections += 1
                return False, round((1 - bucket.tokens) / self._rate, 2)

            bucket.tokens -= 1
            return True, 0.0

    def snapshot(self) -> dict:
        return {
            "perMinute": self.per_minute,
            "trackedCallers": len(self._buckets),
            "rejections": self.rejections,
        }


# ── Circuit breaker ──────────────────────────────────────────────

BreakerState = Literal["closed", "open", "half_open"]


@dataclass
class CircuitBreaker:
    """
    One breaker per upstream service.

    closed    -> calls flow, consecutive failures counted
    open      -> calls rejected immediately until the cooldown elapses
    half_open -> one probe allowed; success closes it, failure re-opens it
    """

    name: str
    threshold: int = CIRCUIT_BREAKER_THRESHOLD
    cooldown: float = CIRCUIT_BREAKER_COOLDOWN
    failures: int = 0
    opened_at: Optional[float] = None
    trips: int = 0
    _probing: bool = field(default=False, repr=False)

    @property
    def state(self) -> BreakerState:
        if self.opened_at is None:
            return "closed"
        if time.monotonic() - self.opened_at >= self.cooldown:
            return "half_open"
        return "open"

    def allows(self) -> bool:
        state = self.state
        if state == "closed":
            return True
        if state == "open":
            return False
        # half_open: admit exactly one probe.
        if self._probing:
            return False
        self._probing = True
        return True

    def record_success(self) -> None:
        self.failures = 0
        self.opened_at = None
        self._probing = False

    def record_failure(self) -> None:
        self._probing = False
        self.failures += 1
        if self.failures >= self.threshold:
            if self.opened_at is None:
                self.trips += 1
            self.opened_at = time.monotonic()

    def retry_after(self) -> float:
        if self.opened_at is None:
            return 0.0
        return max(0.0, round(self.cooldown - (time.monotonic() - self.opened_at), 2))

    def snapshot(self) -> dict:
        return {
            "service": self.name,
            "state": self.state,
            "consecutiveFailures": self.failures,
            "threshold": self.threshold,
            "trips": self.trips,
            "retryAfterSeconds": self.retry_after(),
        }


class CircuitOpen(RuntimeError):
    """The breaker for this upstream is open; the call was not attempted."""

    def __init__(self, breaker: CircuitBreaker) -> None:
        super().__init__(
            f"Circuit open for {breaker.name} after {breaker.failures} consecutive "
            f"failures. Retry in {breaker.retry_after()}s."
        )
        self.breaker = breaker


# ── Singletons ───────────────────────────────────────────────────

rate_limiter = RateLimiter()
_breakers: dict[str, CircuitBreaker] = {}


def breaker_for(service: str) -> CircuitBreaker:
    if service not in _breakers:
        _breakers[service] = CircuitBreaker(name=service)
    return _breakers[service]


def policy_snapshot() -> dict:
    """The live policy, as enforced — not the env vars as configured."""
    return {
        "rateLimit": rate_limiter.snapshot(),
        "timeoutSeconds": TIMEOUT_SECONDS,
        "circuitBreakers": [b.snapshot() for b in _breakers.values()],
        "circuitBreakerThreshold": CIRCUIT_BREAKER_THRESHOLD,
        "circuitBreakerCooldownSeconds": CIRCUIT_BREAKER_COOLDOWN,
        "scope": "per-process (single replica)",
    }
