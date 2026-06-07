import pytest

from les.emulators import (
    LiftEmulatorConfig,
    emulate_reduced_step,
    emulate_trajectory,
    reconstruct_fine_subset,
)
from les_state_reduction import BucketConfig


def test_reconstruct_fine_subset_uses_bucket_midpoint() -> None:
    reduced = {"n": 2.0, "c": 1.0}
    configs = {"n": BucketConfig(min_value=0.0, max_value=10.0, buckets=5)}

    fine = reconstruct_fine_subset(
        reduced,
        fields=("n", "c"),
        bucket_configs=configs,
        scales={"n": 1.0, "c": 0.5},
        offsets={"c": 0.25},
    )

    assert fine == {"n": 5.0, "c": 0.75}


def test_emulate_reduced_step_is_deterministic_and_bounded() -> None:
    config = LiftEmulatorConfig(
        control_gains={"n": {"fertilizer": 1.2}, "c": {"compost": 0.4}},
        leakage={"n": 0.1},
        upper_bounds={"n": 10.0, "c": 10.0},
        lower_bounds={"n": 0.0, "c": 0.0},
        reconstruction_fields=("n", "c"),
    )

    first = emulate_reduced_step(
        {"n": 1.0, "c": 1.0},
        {"fertilizer": 1.0, "compost": 2.0},
        config=config,
    )
    second = emulate_reduced_step(
        {"n": 1.0, "c": 1.0},
        {"fertilizer": 1.0, "compost": 2.0},
        config=config,
    )

    assert first.next_reduced_state == second.next_reduced_state
    assert first.next_reduced_state["n"] == pytest.approx(2.1)
    assert first.next_reduced_state["c"] == 1.8
    assert first.proxy_vector == {"n": 0.0, "c": 0.0}


def test_trajectory_applies_corrections_from_hook() -> None:
    config = LiftEmulatorConfig(
        control_gains={"n": {"fertilizer": 1.0}},
        correction_gain=0.5,
        reconstruction_fields=("n",),
    )

    summary = emulate_trajectory(
        {"n": 1.0},
        [{"fertilizer": 1.0}, {"fertilizer": 0.0}],
        config=config,
        correction_hook=lambda _step, state, _control: {"n": -0.4 if state["n"] > 1.0 else 0.0},
    )

    assert summary.initial_state == {"n": 1.0}
    assert summary.steps[0].next_reduced_state["n"] == 2.0
    assert summary.steps[1].applied_corrections["n"] == -0.2
    assert summary.steps[1].next_reduced_state["n"] == 1.8


def test_trajectory_carries_proxy_series_for_offline_feedback() -> None:
    config = LiftEmulatorConfig(
        control_gains={"n": {"fertilizer": 1.0}, "c": {"compost": 1.0}},
        reconstruction_fields=("n", "c"),
        reconstruction_scales={"n": 2.0},
    )
    summary = emulate_trajectory(
        {"n": 0.0, "c": 1.0},
        [{"fertilizer": 0.0, "compost": 1.0}, {"fertilizer": 1.0, "compost": 0.0}],
        config=config,
    )

    assert summary.proxy_series == (
        {"n": 0.0, "c": 0.0},
        {"n": 1.0, "c": 0.0},
    )
    assert summary.final_state["c"] == 2.0
