import pytest

from les.runners.reduced_runner import ReducedRunner, ReducedRunnerConfig, ReducedState


def test_runner_from_projected_state_preserves_projection_fields() -> None:
    projected = {
        "process_level": 2.5,
        "actuator_level": 0.75,
        "step_index": 8,
        "elapsed_seconds": 12.0,
    }
    runner = ReducedRunner.from_projected_state(projected, subsystem="nutrient")

    assert runner.state == ReducedState(
        subsystem="nutrient",
        process_level=2.5,
        actuator_level=0.75,
        step_index=8,
        elapsed_seconds=12.0,
    )
    assert runner.state.as_projection() == {
        "process_level": 2.5,
        "actuator_level": 0.75,
        "step_index": 8.0,
        "elapsed_seconds": 12.0,
    }


def test_reduced_runner_config_rejects_invalid_ranges() -> None:
    with pytest.raises(ValueError, match="default_dt_seconds"):
        ReducedRunnerConfig(default_dt_seconds=0.0)

    with pytest.raises(ValueError, match="process_min"):
        ReducedRunnerConfig(process_min=1.0, process_max=0.0)

    with pytest.raises(ValueError, match="actuator_min"):
        ReducedRunnerConfig(actuator_min=1.0, actuator_max=0.0)
