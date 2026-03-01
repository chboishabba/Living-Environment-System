from les_state_reduction import (
    BucketConfig,
    SoilBounds,
    SoilBuckets,
    SoilDelta,
    apply_soil_delta_guarded,
    check_monotone_transition,
    enumerate_bucket_states,
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
