from les.contracts_projection import ProjectionContract
from les.examples.recirculation_fast_runner import (
    build_recirculation_comparison_harness,
    build_recirculation_projection_contract,
    calibrate_recirculation_fast_runner,
    compare_recirculation_fast_runner,
)
from les.simulators import DetailedRecirculationControl
from les_state_reduction import ComparisonHarness


def test_recirculation_example_exposes_projection_contract_and_harness() -> None:
    contract = build_recirculation_projection_contract()
    harness = build_recirculation_comparison_harness()

    assert isinstance(contract, ProjectionContract)
    assert isinstance(harness, ComparisonHarness)
    assert contract.retained_variables == (
        "tank_nitrate_mg_l",
        "filter_nitrate_mg_l",
        "pump_flow_l_s",
        "time_s",
    )
    assert harness.keys == ("process_level", "actuator_level", "elapsed_seconds")


def test_recirculation_fast_runner_comparison_returns_proxy_series_without_failure() -> None:
    controls = [
        DetailedRecirculationControl(
            pump_duty=0.5,
            ammonia_input_mg_s=8.0,
            nitrate_dose_mg_s=2.0,
            plant_uptake_mg_s=1.5,
            aeration_duty=0.8,
        )
        for _ in range(8)
    ]

    summary = compare_recirculation_fast_runner(controls)

    assert len(summary.steps) == 9
    assert len(summary.divergence_proxy_series) == 9
    assert summary.first_witness is None


def test_recirculation_fast_runner_surfaces_first_witness_under_strict_tolerance() -> None:
    controls = [
        DetailedRecirculationControl(
            pump_duty=1.0,
            ammonia_input_mg_s=12.0,
            nitrate_dose_mg_s=3.0,
            plant_uptake_mg_s=0.0,
            aeration_duty=1.0,
        )
        for _ in range(4)
    ]
    strict_harness = build_recirculation_comparison_harness(
        l1_tolerance=0.1,
        linf_tolerance=0.05,
    )

    summary = compare_recirculation_fast_runner(controls, harness=strict_harness)

    assert summary.first_witness is not None
    assert summary.first_witness.proxy_vector


def test_recirculation_fast_runner_can_self_tune_conservatively() -> None:
    controls = [
        DetailedRecirculationControl(
            pump_duty=0.3 + (0.1 * (index % 3)),
            ammonia_input_mg_s=6.0 + index,
            nitrate_dose_mg_s=1.0 + (0.5 * (index % 2)),
            plant_uptake_mg_s=1.0,
            aeration_duty=0.7 + (0.05 * (index % 2)),
        )
        for index in range(10)
    ]

    result = calibrate_recirculation_fast_runner(controls)

    assert result.accepted is True
    assert result.calibrated.summary.first_witness is None
    assert (
        result.calibrated.summary.max_l1_divergence
        < result.baseline.summary.max_l1_divergence
    )
    assert result.calibrated.config.actuator_response >= 0.0
    assert result.calibrated.config.passive_decay >= 0.0


def test_recirculation_fast_runner_rejects_non_improving_candidate() -> None:
    controls = [
        DetailedRecirculationControl(
            pump_duty=0.6,
            ammonia_input_mg_s=7.0,
            nitrate_dose_mg_s=0.0,
            plant_uptake_mg_s=0.5,
            aeration_duty=0.9,
        )
        for _ in range(2)
    ]
    strict_harness = build_recirculation_comparison_harness(
        l1_tolerance=1e-6,
        linf_tolerance=1e-6,
    )

    result = calibrate_recirculation_fast_runner(controls, harness=strict_harness)

    assert result.accepted is False
    assert result.calibrated.config == result.baseline.config
