"""State reduction scaffolding for LES bucketed dynamics.

This module translates continuous or high-dimensional state into discrete
buckets, enforces invariants, and offers runtime checks for monotone
transitions. It is intentionally lightweight so it can be imported into
optimizers or simulations without heavy dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Sequence

from les.contracts import Counterexample, InvariantEnvelope


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


ProjectionFn = Callable[[Mapping[str, float]], Mapping[str, float]]
ReducedInvariant = Callable[[Mapping[str, float]], bool]


@dataclass(frozen=True)
class DivergenceWitness:
    """Counterexample-style witness for reduced-runner divergence."""

    step: int
    message: str
    projected_detailed: Mapping[str, float]
    reduced_state: Mapping[str, float]
    proxy_vector: Mapping[str, float]
    failing_invariants: tuple[str, ...]
    counterexample: Counterexample | None = None


@dataclass(frozen=True)
class StepComparison:
    """Per-step comparison between projected detailed state and reduced state."""

    step: int
    projected_detailed: Mapping[str, float]
    reduced_state: Mapping[str, float]
    proxy_vector: Mapping[str, float]
    l1_divergence: float
    linf_divergence: float
    failing_invariants: tuple[str, ...]


@dataclass(frozen=True)
class ComparisonSummary:
    """Aggregate comparison result for detailed vs reduced trajectories."""

    steps: tuple[StepComparison, ...]
    first_witness: DivergenceWitness | None

    @property
    def max_l1_divergence(self) -> float:
        if not self.steps:
            return 0.0
        return max(step.l1_divergence for step in self.steps)

    @property
    def max_linf_divergence(self) -> float:
        if not self.steps:
            return 0.0
        return max(step.linf_divergence for step in self.steps)

    @property
    def divergence_proxy_series(self) -> tuple[Mapping[str, float], ...]:
        return tuple(step.proxy_vector for step in self.steps)


@dataclass(frozen=True)
class ComparisonHarness:
    """Reusable validation seam for detailed-vs-reduced trajectory checks."""

    invariants: tuple[tuple[str, ReducedInvariant], ...] = ()
    envelope: InvariantEnvelope | None = None
    projection: ProjectionFn | None = None
    keys: tuple[str, ...] | None = None
    l1_tolerance: float | None = None
    linf_tolerance: float | None = None

    def compare(
        self,
        detailed_states: Sequence[Mapping[str, float]],
        reduced_states: Sequence[Mapping[str, float]],
    ) -> ComparisonSummary:
        """Run the configured comparison surface over two aligned trajectories."""
        return compare_projected_trajectory(
            detailed_states,
            reduced_states,
            invariants=self.invariants,
            envelope=self.envelope,
            projection=self.projection,
            keys=self.keys,
            l1_tolerance=self.l1_tolerance,
            linf_tolerance=self.linf_tolerance,
        )


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


def project_soil_buckets(state: SoilBuckets) -> dict[str, float]:
    """Project bucketed soil state into a numeric reduced-state surface."""
    return {
        "n": float(state.n),
        "c": float(state.c),
        "s": float(state.s),
        "d": float(state.d),
        "f": float(state.f),
    }


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


def divergence_proxy_vector(
    projected_detailed: Mapping[str, float],
    reduced_state: Mapping[str, float],
    keys: Sequence[str] | None = None,
) -> dict[str, float]:
    """Return a cheap signed proxy vector: detailed projection minus reduced state."""
    if keys is None:
        keys = tuple(sorted(set(projected_detailed) & set(reduced_state)))
    proxy: dict[str, float] = {}
    for key in keys:
        proxy[key] = float(projected_detailed[key]) - float(reduced_state[key])
    return proxy


def _collect_counterexamples(
    subject: str,
    state_values: Mapping[str, float],
    invariants: Sequence[tuple[str, ReducedInvariant]],
) -> list[Counterexample]:
    failures: list[Counterexample] = []
    for name, invariant in invariants:
        try:
            ok = invariant(state_values)
        except Exception as exc:  # pragma: no cover - defensive path
            failures.append(
                Counterexample(
                    subject=subject,
                    predicate=name,
                    witness=dict(state_values),
                    message=f"invariant raised: {exc}",
                )
            )
            continue
        if not ok:
            failures.append(
                Counterexample(
                    subject=subject,
                    predicate=name,
                    witness=dict(state_values),
                    message=f"invariant {name!r} failed",
                )
            )
    return failures


def compare_projected_trajectory(
    detailed_states: Sequence[Mapping[str, float]],
    reduced_states: Sequence[Mapping[str, float]],
    *,
    invariants: Sequence[tuple[str, ReducedInvariant]] = (),
    envelope: InvariantEnvelope | None = None,
    projection: ProjectionFn | None = None,
    keys: Sequence[str] | None = None,
    l1_tolerance: float | None = None,
    linf_tolerance: float | None = None,
) -> ComparisonSummary:
    """Compare a detailed trajectory against a reduced one on a projected surface.

    This is the core fast-runner validation surface:
    1. project detailed state into reduced coordinates
    2. compute a cheap divergence proxy vector
    3. surface first tolerance or invariant failure as a witness
    """
    if len(detailed_states) != len(reduced_states):
        raise ValueError("detailed_states and reduced_states must have the same length")
    if projection is None:
        projection = lambda state: state
    active_invariants = envelope.invariants if envelope is not None else invariants
    witness_subject = envelope.name if envelope is not None else "comparison"

    comparisons: list[StepComparison] = []
    first_witness: DivergenceWitness | None = None

    for step, (detailed, reduced) in enumerate(zip(detailed_states, reduced_states)):
        projected = projection(detailed)
        proxy = divergence_proxy_vector(projected, reduced, keys=keys)
        abs_values = [abs(value) for value in proxy.values()]
        l1 = sum(abs_values)
        linf = max(abs_values, default=0.0)

        counterexamples = _collect_counterexamples(
            witness_subject, reduced, active_invariants
        )
        failing_invariants = tuple(example.predicate for example in counterexamples)

        comparisons.append(
            StepComparison(
                step=step,
                projected_detailed=dict(projected),
                reduced_state=dict(reduced),
                proxy_vector=proxy,
                l1_divergence=l1,
                linf_divergence=linf,
                failing_invariants=failing_invariants,
            )
        )

        if first_witness is not None:
            continue

        tolerance_failures: list[str] = []
        if l1_tolerance is not None and l1 > l1_tolerance:
            tolerance_failures.append(f"l1>{l1_tolerance}")
        if linf_tolerance is not None and linf > linf_tolerance:
            tolerance_failures.append(f"linf>{linf_tolerance}")

        if tolerance_failures or failing_invariants:
            reasons = tolerance_failures + list(failing_invariants)
            first_witness = DivergenceWitness(
                step=step,
                message=", ".join(reasons),
                projected_detailed=dict(projected),
                reduced_state=dict(reduced),
                proxy_vector=proxy,
                failing_invariants=failing_invariants,
                counterexample=counterexamples[0] if counterexamples else None,
            )

    return ComparisonSummary(steps=tuple(comparisons), first_witness=first_witness)


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
