from les_state_reduction import (
    BucketConfig,
    ComparisonSummary,
    SoilBounds,
    SoilBuckets,
    SoilDelta,
    apply_soil_delta_guarded,
    check_monotone_transition,
    compare_projected_trajectory,
    divergence_proxy_vector,
    enumerate_bucket_states,
    project_soil_buckets,
)


def test_bucketize_clamps() -> None:
    cfg = BucketConfig(min_value=0.0, max_value=10.0, buckets=5)
    assert cfg.bucketize(-1.0) == 0
    assert cfg.bucketize(0.0) == 0
    assert cfg.bucketize(10.0) == 4
    assert cfg.clamp_bucket(99) == 4


def test_guarded_transition_raises_on_invariant() -> None:
    state = SoilBuckets(n=2, c=2, s=2, d=0, f=0)
    delta = SoilDelta(dn=-1, dc=0, ds=0, dd=0)
    limits = {"n": 5, "c": 5, "s": 5, "d": 0}
    bounds = SoilBounds(min_n=2, min_c=2, min_s=2, max_d=None)
    try:
        apply_soil_delta_guarded(state, delta, limits, bounds)
    except ValueError:
        return
    assert False, "Expected guarded transition to raise on invariant violation"


def test_monotone_transition_holds_for_increment() -> None:
    limits = {"n": 1, "c": 1, "s": 1, "d": 1}
    states = enumerate_bucket_states(limits, families=[0])

    def transition(s: SoilBuckets) -> SoilBuckets:
        return SoilBuckets(
            n=min(limits["n"], s.n + 1),
            c=min(limits["c"], s.c + 1),
            s=min(limits["s"], s.s + 1),
            d=min(limits["d"], s.d + 1),
            f=s.f,
        )

    violations = check_monotone_transition(states, transition)
    assert violations == []


def test_monotone_transition_detects_violation() -> None:
    states = [SoilBuckets(n=0, c=0, s=0, d=0, f=0), SoilBuckets(n=1, c=0, s=0, d=0, f=0)]

    def transition(s: SoilBuckets) -> SoilBuckets:
        flipped = 1 if s.n == 0 else 0
        return SoilBuckets(n=flipped, c=s.c, s=s.s, d=s.d, f=s.f)

    violations = check_monotone_transition(states, transition)
    assert violations


def test_divergence_proxy_vector_is_signed_difference() -> None:
    projected = {"n": 3.0, "c": 2.0, "s": 4.0}
    reduced = {"n": 2.5, "c": 3.0, "s": 4.0}

    proxy = divergence_proxy_vector(projected, reduced)

    assert proxy == {"c": -1.0, "n": 0.5, "s": 0.0}


def test_compare_projected_trajectory_returns_first_witness() -> None:
    detailed = [
        {"n": 2.0, "c": 2.0, "s": 2.0},
        {"n": 3.0, "c": 2.0, "s": 1.0},
    ]
    reduced = [
        {"n": 2.0, "c": 2.0, "s": 2.0},
        {"n": 1.0, "c": 2.0, "s": 1.0},
    ]

    summary = compare_projected_trajectory(
        detailed,
        reduced,
        invariants=[("soil_floor", lambda state: state["n"] >= 2.0)],
        l1_tolerance=1.0,
        linf_tolerance=1.0,
    )

    assert isinstance(summary, ComparisonSummary)
    assert len(summary.steps) == 2
    assert summary.first_witness is not None
    assert summary.first_witness.step == 1
    assert summary.first_witness.proxy_vector["n"] == 2.0
    assert "l1>1.0" in summary.first_witness.message
    assert summary.first_witness.failing_invariants == ("soil_floor",)


def test_compare_projected_trajectory_exposes_proxy_series_for_offline_use() -> None:
    detailed = [
        project_soil_buckets(SoilBuckets(n=2, c=3, s=4, d=0, f=0)),
        project_soil_buckets(SoilBuckets(n=3, c=3, s=4, d=0, f=0)),
    ]
    reduced = [
        {"n": 2.0, "c": 2.5, "s": 4.0, "d": 0.0, "f": 0.0},
        {"n": 2.0, "c": 3.0, "s": 3.0, "d": 0.0, "f": 0.0},
    ]

    summary = compare_projected_trajectory(detailed, reduced)

    assert summary.first_witness is None
    assert summary.divergence_proxy_series == (
        {"c": 0.5, "d": 0.0, "f": 0.0, "n": 0.0, "s": 0.0},
        {"c": 0.0, "d": 0.0, "f": 0.0, "n": 1.0, "s": 1.0},
    )
    assert summary.max_l1_divergence == 2.0
    assert summary.max_linf_divergence == 1.0
