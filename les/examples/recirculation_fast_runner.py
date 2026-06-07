"""Worked example: detailed recirculation vs reduced fast runner."""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Iterable, Sequence

from les.contracts import InvariantEnvelope
from les.contracts_projection import ProjectionContract, ProjectionSummaryStatistic
from les.runners import ReducedRunner, ReducedRunnerConfig
from les.simulators import (
    DetailedRecirculationConfig,
    DetailedRecirculationControl,
    DetailedRecirculationSimulator,
)
from les_state_reduction import ComparisonHarness, ComparisonSummary


@dataclass(frozen=True)
class CalibrationCandidate:
    """One proposed reduced-runner update derived from detailed traces."""

    config: ReducedRunnerConfig
    residual_correction: float
    summary: ComparisonSummary


@dataclass(frozen=True)
class RecirculationCalibrationResult:
    """Outcome of conservative self-tuning for the recirculation fast runner."""

    baseline: CalibrationCandidate
    calibrated: CalibrationCandidate
    accepted: bool
    reason: str


def project_recirculation_state(full_state: dict[str, float]) -> dict[str, float]:
    """Project detailed recirculation state into a reduced runner surface."""
    return {
        "process_level": (
            float(full_state["tank_nitrate_mg_l"]) + float(full_state["filter_nitrate_mg_l"])
        )
        / 2.0,
        "actuator_level": float(full_state["pump_flow_l_s"]),
        "step_index": float(round(float(full_state["time_s"]) * 2.0)),
        "elapsed_seconds": float(full_state["time_s"]),
    }


def build_recirculation_projection_contract(
    *,
    dt_s: float = 0.5,
) -> ProjectionContract:
    """Formal full_state -> reduced_state seam for the recirculation example."""
    steps_per_second = 1.0 / dt_s
    return ProjectionContract(
        name="les.examples.recirculation.projection",
        projection=lambda state: {
            "process_level": (
                float(state["tank_nitrate_mg_l"]) + float(state["filter_nitrate_mg_l"])
            )
            / 2.0,
            "actuator_level": float(state["pump_flow_l_s"]),
            "step_index": float(round(float(state["time_s"]) * steps_per_second)),
            "elapsed_seconds": float(state["time_s"]),
        },
        retained_variables=(
            "tank_nitrate_mg_l",
            "filter_nitrate_mg_l",
            "pump_flow_l_s",
            "time_s",
        ),
        discarded_variables=(
            "tank_ammonia_mg_l",
            "filter_ammonia_mg_l",
            "tank_do_mg_l",
            "filter_do_mg_l",
            "cumulative_recirculated_l",
            "cumulative_ammonia_input_mg",
            "cumulative_nitrate_dosed_mg",
            "cumulative_uptake_mg",
            "cumulative_nitrified_mg",
        ),
        summary_statistics=(
            ProjectionSummaryStatistic(
                name="nitrate_spread",
                source="full_state",
                compute=lambda full: abs(
                    float(full["tank_nitrate_mg_l"]) - float(full["filter_nitrate_mg_l"])
                ),
            ),
        ),
        description="Maps fine recirculation state onto coarse process/actuator coordinates.",
    )


def build_recirculation_invariant_envelope() -> InvariantEnvelope:
    """Admissible operating envelope for the recirculation fast-runner surface."""
    return InvariantEnvelope.from_iterables(
        name="les.examples.recirculation.admissible",
        lane="validation",
        invariants=(
            ("nonnegative_process", lambda state: float(state["process_level"]) >= 0.0),
            ("bounded_actuator", lambda state: 0.0 <= float(state["actuator_level"]) <= 2.5),
            ("monotone_time", lambda state: float(state["elapsed_seconds"]) >= 0.0),
        ),
        description="Basic admissibility for reduced recirculation trajectories.",
    )


def build_recirculation_comparison_harness(
    *,
    dt_s: float = 0.5,
    l1_tolerance: float = 6.0,
    linf_tolerance: float = 2.5,
) -> ComparisonHarness:
    """Comparison harness binding the recirculation projection and envelope."""
    contract = build_recirculation_projection_contract(dt_s=dt_s)
    return ComparisonHarness(
        envelope=build_recirculation_invariant_envelope(),
        projection=contract.project_state,
        keys=("process_level", "actuator_level", "elapsed_seconds"),
        l1_tolerance=l1_tolerance,
        linf_tolerance=linf_tolerance,
    )


def simulate_detailed_recirculation(
    controls: Iterable[DetailedRecirculationControl],
    *,
    config: DetailedRecirculationConfig | None = None,
) -> tuple[dict[str, float], ...]:
    """Run the detailed simulator and return snapshots including the initial state."""
    simulator = DetailedRecirculationSimulator(config=config)
    states = simulator.run(tuple(controls), include_initial=True)
    return tuple(asdict(state) for state in states)


def run_reduced_recirculation(
    controls: Sequence[DetailedRecirculationControl],
    *,
    config: ReducedRunnerConfig | None = None,
    projection_contract: ProjectionContract | None = None,
    initial_detailed_state: dict[str, float] | None = None,
    process_correction: float = 0.0,
) -> tuple[dict[str, float], ...]:
    """Run the reduced fast runner over the same control sequence."""
    projection_contract = projection_contract or build_recirculation_projection_contract()
    config = config or ReducedRunnerConfig(default_dt_seconds=0.5)
    initial_surface = initial_detailed_state or DetailedRecirculationSimulator().snapshot()
    runner = ReducedRunner.from_projected_state(
        projection_contract.project_state(initial_surface),
        subsystem="recirculation",
        config=config,
    )
    series = [runner.state.as_projection()]
    for control in controls:
        state = runner.step(
            control_input=control.pump_duty * 2.5,
            dt_seconds=config.default_dt_seconds,
        )
        if process_correction:
            corrected_process = min(
                config.process_max,
                max(config.process_min, state.process_level + process_correction),
            )
            state = replace(runner.state, process_level=corrected_process)
            runner.state = state
        series.append(state.as_projection())
    return tuple(series)


def _score_summary(summary: ComparisonSummary) -> tuple[float, float]:
    """Return a compact comparison score; lower is better."""
    return (summary.max_l1_divergence, summary.max_linf_divergence)


def _is_better_summary(candidate: ComparisonSummary, baseline: ComparisonSummary) -> bool:
    """Prefer lower divergence and no newly introduced witness."""
    if candidate.first_witness is not None and baseline.first_witness is None:
        return False
    return _score_summary(candidate) < _score_summary(baseline)


def _solve_3x3(system: Sequence[Sequence[float]], rhs: Sequence[float]) -> tuple[float, float, float]:
    """Solve a 3x3 linear system using Gaussian elimination."""
    matrix = [list(row) + [float(rhs[index])] for index, row in enumerate(system)]
    size = 3
    for pivot_index in range(size):
        pivot_row = max(range(pivot_index, size), key=lambda row: abs(matrix[row][pivot_index]))
        pivot = matrix[pivot_row][pivot_index]
        if abs(pivot) < 1e-12:
            raise ValueError("singular calibration system")
        if pivot_row != pivot_index:
            matrix[pivot_index], matrix[pivot_row] = matrix[pivot_row], matrix[pivot_index]
        pivot = matrix[pivot_index][pivot_index]
        for column in range(pivot_index, size + 1):
            matrix[pivot_index][column] /= pivot
        for row in range(size):
            if row == pivot_index:
                continue
            factor = matrix[row][pivot_index]
            if factor == 0.0:
                continue
            for column in range(pivot_index, size + 1):
                matrix[row][column] -= factor * matrix[pivot_index][column]
    return (matrix[0][size], matrix[1][size], matrix[2][size])


def _fit_reduced_runner_config(
    projected_states: Sequence[dict[str, float]],
    controls: Sequence[DetailedRecirculationControl],
    *,
    base_config: ReducedRunnerConfig,
    actuator_max: float,
) -> ReducedRunnerConfig:
    """Fit affine reduced dynamics from projected detailed traces."""
    if len(projected_states) != len(controls) + 1:
        raise ValueError("projected_states must include the initial state")

    xx = xu = xb = uu = ub = bb = xy = uy = by = 0.0
    dt = base_config.default_dt_seconds

    for current, nxt, control in zip(projected_states, projected_states[1:], controls):
        x = float(current["process_level"])
        u = float(control.pump_duty) * actuator_max
        y = (float(nxt["process_level"]) - x) / dt

        xx += x * x
        xu += x * u
        xb += x
        uu += u * u
        ub += u
        bb += 1.0
        xy += x * y
        uy += u * y
        by += y

    gain, negative_decay, bias = _solve_3x3(
        (
            (uu, xu, ub),
            (xu, xx, xb),
            (ub, xb, bb),
        ),
        (uy, xy, by),
    )
    return ReducedRunnerConfig(
        default_dt_seconds=base_config.default_dt_seconds,
        actuator_response=max(0.0, gain),
        passive_decay=max(0.0, -negative_decay),
        process_bias=bias,
        process_min=base_config.process_min,
        process_max=base_config.process_max,
        actuator_min=base_config.actuator_min,
        actuator_max=base_config.actuator_max,
    )


def _estimate_residual_correction(
    projected_states: Sequence[dict[str, float]],
    reduced_states: Sequence[dict[str, float]],
) -> float:
    """Estimate a cheap constant correction from the divergence proxy series."""
    if len(projected_states) != len(reduced_states):
        raise ValueError("projected_states and reduced_states must align")
    if len(projected_states) <= 1:
        return 0.0
    residual_sum = 0.0
    for projected, reduced in zip(projected_states[1:], reduced_states[1:]):
        residual_sum += float(projected["process_level"]) - float(reduced["process_level"])
    return residual_sum / float(len(projected_states) - 1)


def compare_recirculation_fast_runner(
    controls: Sequence[DetailedRecirculationControl],
    *,
    simulator_config: DetailedRecirculationConfig | None = None,
    runner_config: ReducedRunnerConfig | None = None,
    harness: ComparisonHarness | None = None,
    process_correction: float = 0.0,
) -> ComparisonSummary:
    """Run the worked detailed-vs-reduced example and compare trajectories."""
    simulator_config = simulator_config or DetailedRecirculationConfig()
    projection_contract = build_recirculation_projection_contract(dt_s=simulator_config.dt_s)
    detailed_states = simulate_detailed_recirculation(controls, config=simulator_config)
    if runner_config is None:
        runner_config = ReducedRunnerConfig(
            default_dt_seconds=simulator_config.dt_s,
            actuator_response=0.12,
            passive_decay=0.015,
            process_bias=0.02,
            process_min=0.0,
            process_max=20.0,
            actuator_min=0.0,
            actuator_max=simulator_config.pump_max_flow_l_s,
        )
    reduced_states = run_reduced_recirculation(
        controls,
        config=runner_config,
        projection_contract=projection_contract,
        initial_detailed_state=detailed_states[0],
        process_correction=process_correction,
    )
    harness = harness or build_recirculation_comparison_harness(
        dt_s=simulator_config.dt_s
    )
    return harness.compare(detailed_states, reduced_states)


def calibrate_recirculation_fast_runner(
    controls: Sequence[DetailedRecirculationControl],
    *,
    simulator_config: DetailedRecirculationConfig | None = None,
    baseline_config: ReducedRunnerConfig | None = None,
    harness: ComparisonHarness | None = None,
) -> RecirculationCalibrationResult:
    """Conservatively fit and accept a reduced-runner update only if it improves."""
    simulator_config = simulator_config or DetailedRecirculationConfig()
    projection_contract = build_recirculation_projection_contract(dt_s=simulator_config.dt_s)
    harness = harness or build_recirculation_comparison_harness(dt_s=simulator_config.dt_s)

    detailed_states = simulate_detailed_recirculation(controls, config=simulator_config)
    projected_states = tuple(
        projection_contract.project_state(state) for state in detailed_states
    )

    if baseline_config is None:
        baseline_config = ReducedRunnerConfig(
            default_dt_seconds=simulator_config.dt_s,
            actuator_response=0.12,
            passive_decay=0.015,
            process_bias=0.02,
            process_min=0.0,
            process_max=20.0,
            actuator_min=0.0,
            actuator_max=simulator_config.pump_max_flow_l_s,
        )

    baseline_reduced = run_reduced_recirculation(
        controls,
        config=baseline_config,
        projection_contract=projection_contract,
        initial_detailed_state=detailed_states[0],
        process_correction=0.0,
    )
    baseline_summary = harness.compare(detailed_states, baseline_reduced)
    baseline = CalibrationCandidate(
        config=baseline_config,
        residual_correction=0.0,
        summary=baseline_summary,
    )

    try:
        fitted_config = _fit_reduced_runner_config(
            projected_states,
            controls,
            base_config=baseline_config,
            actuator_max=simulator_config.pump_max_flow_l_s,
        )
    except ValueError:
        return RecirculationCalibrationResult(
            baseline=baseline,
            calibrated=baseline,
            accepted=False,
            reason="rejected calibrated update because the fitting system was underdetermined",
        )
    fitted_reduced = run_reduced_recirculation(
        controls,
        config=fitted_config,
        projection_contract=projection_contract,
        initial_detailed_state=detailed_states[0],
        process_correction=0.0,
    )
    fitted_correction = _estimate_residual_correction(projected_states, fitted_reduced)
    corrected_reduced = run_reduced_recirculation(
        controls,
        config=fitted_config,
        projection_contract=projection_contract,
        initial_detailed_state=detailed_states[0],
        process_correction=fitted_correction,
    )
    calibrated_summary = harness.compare(detailed_states, corrected_reduced)
    calibrated = CalibrationCandidate(
        config=fitted_config,
        residual_correction=fitted_correction,
        summary=calibrated_summary,
    )

    if calibrated_summary.first_witness is not None and baseline_summary.first_witness is None:
        return RecirculationCalibrationResult(
            baseline=baseline,
            calibrated=baseline,
            accepted=False,
            reason="rejected calibrated update because it violated the admissible envelope",
        )
    if not _is_better_summary(calibrated_summary, baseline_summary):
        return RecirculationCalibrationResult(
            baseline=baseline,
            calibrated=baseline,
            accepted=False,
            reason="rejected calibrated update because it did not improve divergence",
        )
    return RecirculationCalibrationResult(
        baseline=baseline,
        calibrated=calibrated,
        accepted=True,
        reason="accepted calibrated update because it reduced divergence without new witness",
    )
