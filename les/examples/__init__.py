"""Worked LES examples that compose detailed and reduced formal surfaces."""

from .recirculation_fast_runner import (
    build_recirculation_comparison_harness,
    build_recirculation_invariant_envelope,
    build_recirculation_projection_contract,
    calibrate_recirculation_fast_runner,
    compare_recirculation_fast_runner,
    project_recirculation_state,
    RecirculationCalibrationResult,
    run_reduced_recirculation,
    simulate_detailed_recirculation,
)

__all__ = [
    "build_recirculation_comparison_harness",
    "build_recirculation_invariant_envelope",
    "build_recirculation_projection_contract",
    "calibrate_recirculation_fast_runner",
    "compare_recirculation_fast_runner",
    "project_recirculation_state",
    "RecirculationCalibrationResult",
    "run_reduced_recirculation",
    "simulate_detailed_recirculation",
]
