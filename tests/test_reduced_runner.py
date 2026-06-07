from les.runners.reduced_runner import (
    ReducedRunner,
    ReducedRunnerConfig,
    ReducedState,
    step_reduced_state,
)


def test_step_reduced_state_advances_deterministically() -> None:
    cfg = ReducedRunnerConfig(
        actuator_response=1.2,
        passive_decay=0.2,
        process_bias=0.1,
        process_min=0.0,
        process_max=10.0,
        actuator_min=0.0,
        actuator_max=1.0,
    )
    state = ReducedState(
        subsystem="pump",
        process_level=4.0,
        actuator_level=0.0,
    )

    next_state = step_reduced_state(
        state,
        control_input=0.5,
        dt_seconds=2.0,
        config=cfg,
    )

    assert next_state.subsystem == "pump"
    assert next_state.process_level == 3.8
    assert next_state.actuator_level == 0.5
    assert next_state.step_index == 1
    assert next_state.elapsed_seconds == 2.0


def test_step_reduced_state_clamps_control_and_process_bounds() -> None:
    cfg = ReducedRunnerConfig(
        actuator_response=5.0,
        passive_decay=0.0,
        process_bias=0.0,
        process_min=0.0,
        process_max=2.0,
        actuator_min=0.1,
        actuator_max=0.9,
    )
    state = ReducedState(subsystem="nutrient", process_level=1.5, actuator_level=0.0)

    upper = step_reduced_state(state, control_input=9.0, dt_seconds=1.0, config=cfg)
    lower = step_reduced_state(state, control_input=-9.0, dt_seconds=1.0, config=cfg)

    assert upper.actuator_level == 0.9
    assert upper.process_level == 2.0
    assert lower.actuator_level == 0.1


def test_reduced_runner_uses_default_dt_and_updates_state() -> None:
    runner = ReducedRunner(
        state=ReducedState(subsystem="generic", process_level=1.0, actuator_level=0.0),
        config=ReducedRunnerConfig(default_dt_seconds=0.5, actuator_response=2.0, passive_decay=0.0),
    )

    state = runner.step(control_input=0.25)

    assert state.process_level == 1.25
    assert state.step_index == 1
    assert state.elapsed_seconds == 0.5
    assert runner.state == state
