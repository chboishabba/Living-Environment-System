"""State reduction scaffolding for LES bucketed dynamics.

This module translates continuous or high-dimensional state into discrete
buckets, enforces invariants, and offers runtime checks for monotone
transitions. It is intentionally lightweight so it can be imported into
optimizers or simulations without heavy dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class BucketConfig:
    """Defines a 1D bucketization scheme for a continuous variable."""

    min_value: float
    max_value: float
    buckets: int

    def bucketize(self, value: float) -> int:
        if self.buckets <= 1:
            return 0
        clamped = max(self.min_value, min(self.max_value, value))
        span = self.max_value - self.min_value
        if span <= 0:
            return 0
        normalized = (clamped - self.min_value) / span
        index = int(normalized * self.buckets)
        return self.clamp_bucket(index)

    def clamp_bucket(self, bucket: int) -> int:
        if self.buckets <= 1:
            return 0
        return max(0, min(self.buckets - 1, bucket))

    def midpoint(self, bucket: int) -> float:
        if self.buckets <= 1:
            return self.min_value
        bucket = self.clamp_bucket(bucket)
        span = self.max_value - self.min_value
        step = span / self.buckets
        return self.min_value + (bucket + 0.5) * step

    def refine(self, factor: int) -> "BucketConfig":
        if factor <= 1:
            return self
        return BucketConfig(
            min_value=self.min_value, max_value=self.max_value, buckets=self.buckets * factor
        )


@dataclass(frozen=True)
class SoilBuckets:
    n: int
    c: int
    s: int
    d: int
    f: int

    def as_tuple(self) -> tuple[int, int, int, int, int]:
        return (self.n, self.c, self.s, self.d, self.f)


@dataclass(frozen=True)
class SoilDelta:
    dn: int = 0
    dc: int = 0
    ds: int = 0
    dd: int = 0


@dataclass(frozen=True)
class SoilBounds:
    min_n: int
    min_c: int
    min_s: int
    max_d: int | None = None


def reduce_raw_soil(
    raw: Mapping[str, float],
    configs: Mapping[str, BucketConfig],
    family: int = 0,
) -> SoilBuckets:
    """Reduce continuous soil state to buckets using provided configs."""
    n = configs["n"].bucketize(raw.get("n", configs["n"].min_value))
    c = configs["c"].bucketize(raw.get("c", configs["c"].min_value))
    s = configs["s"].bucketize(raw.get("s", configs["s"].min_value))
    d = configs["d"].bucketize(raw.get("d", configs["d"].min_value))
    return SoilBuckets(n=n, c=c, s=s, d=d, f=family)


def canonical_rotation_phase(step: int, period: int) -> int:
    """Canonicalize periodic state such as rotation phase or season index."""
    if period <= 0:
        raise ValueError("period must be positive")
    return step % period


def combine_severity(*levels: int) -> int:
    """Monotone combination rule: worst-case (max) severity wins."""
    if not levels:
        return 0
    return max(levels)


def apply_soil_delta(
    state: SoilBuckets,
    delta: SoilDelta,
    limits: Mapping[str, int],
) -> SoilBuckets:
    """Apply bucket deltas with clamping to variable limits."""
    n = max(0, min(limits["n"], state.n + delta.dn))
    c = max(0, min(limits["c"], state.c + delta.dc))
    s = max(0, min(limits["s"], state.s + delta.ds))
    d = max(0, min(limits["d"], state.d + delta.dd))
    return SoilBuckets(n=n, c=c, s=s, d=d, f=state.f)


def check_soil_invariants(state: SoilBuckets, bounds: SoilBounds) -> bool:
    if state.n < bounds.min_n or state.c < bounds.min_c or state.s < bounds.min_s:
        return False
    if bounds.max_d is not None and state.d > bounds.max_d:
        return False
    return True


def apply_soil_delta_guarded(
    state: SoilBuckets,
    delta: SoilDelta,
    limits: Mapping[str, int],
    bounds: SoilBounds,
) -> SoilBuckets:
    """Apply deltas and enforce invariants (guarded transitions)."""
    updated = apply_soil_delta(state, delta, limits)
    if not check_soil_invariants(updated, bounds):
        raise ValueError("Soil invariant violated by transition")
    return updated


def is_componentwise_leq(a: SoilBuckets, b: SoilBuckets) -> bool:
    return a.n <= b.n and a.c <= b.c and a.s <= b.s and a.d <= b.d


def check_monotone_transition(
    states: Sequence[SoilBuckets],
    transition: Callable[[SoilBuckets], SoilBuckets],
) -> list[tuple[SoilBuckets, SoilBuckets]]:
    """Return pairs that violate monotonicity under the provided transition."""
    violations: list[tuple[SoilBuckets, SoilBuckets]] = []
    for i, a in enumerate(states):
        for b in states[i + 1 :]:
            if not is_componentwise_leq(a, b):
                continue
            ta = transition(a)
            tb = transition(b)
            if not is_componentwise_leq(ta, tb):
                violations.append((a, b))
    return violations


def enumerate_bucket_states(
    limits: Mapping[str, int], families: Iterable[int]
) -> list[SoilBuckets]:
    """Helper to enumerate a small bucketed state space for monotonicity checks."""
    states: list[SoilBuckets] = []
    for n in range(limits["n"] + 1):
        for c in range(limits["c"] + 1):
            for s in range(limits["s"] + 1):
                for d in range(limits["d"] + 1):
                    for f in families:
                        states.append(SoilBuckets(n=n, c=c, s=s, d=d, f=f))
    return states
