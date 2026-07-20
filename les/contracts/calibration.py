"""Simulator-to-latent calibration contracts for LES."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from .planning_receipt import EscalationEvidence

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")
LatentT = TypeVar("LatentT")


@dataclass(frozen=True)
class ModelIdentity:
    name: str
    version: str
    source_revision: str
    configuration_hash: str
    authority_class: str


@dataclass(frozen=True)
class InputDomain:
    name: str
    variable_names: tuple[str, ...]
    unit_declarations: tuple[str, ...]
    spatial_extent: str
    temporal_extent: str
    parameter_bounds: tuple[str, ...]
    exclusions: tuple[str, ...] = ()


@dataclass(frozen=True)
class TrainingCoverage:
    scenario_count: int
    climate_regimes: tuple[str, ...]
    soil_regimes: tuple[str, ...]
    management_regimes: tuple[str, ...]
    intervention_regimes: tuple[str, ...]
    held_out_scenario_count: int
    coverage_reference: str


@dataclass(frozen=True)
class HeldOutValidation:
    dataset: str
    sample_count: int
    error_bound: float
    observed_maximum_error: float
    calibration_method: str
    calibration_reference: str

    @property
    def passes(self) -> bool:
        return self.observed_maximum_error <= self.error_bound


@dataclass(frozen=True)
class LatentModel(Generic[InputT, LatentT, OutputT]):
    encode: Callable[[InputT], LatentT]
    predict: Callable[[LatentT], OutputT]
    uncertainty: Callable[[LatentT], float]
    inside_declared_support: Callable[[InputT], bool]


@dataclass(frozen=True)
class CalibrationReceipt(Generic[InputT, LatentT, OutputT]):
    authoritative_model: ModelIdentity
    input_domain: InputDomain
    coverage: TrainingCoverage
    output_names: tuple[str, ...]
    output_units: tuple[str, ...]
    latent_model: LatentModel[InputT, LatentT, OutputT]
    held_out: HeldOutValidation
    uncertainty_threshold: float
    residual_threshold: float
    escalation_policy: str
    provenance: tuple[str, ...]

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.held_out.passes:
            errors.append("held-out maximum error exceeds declared bound")
        if self.coverage.scenario_count <= 0:
            errors.append("training scenario count must be positive")
        if self.coverage.held_out_scenario_count <= 0:
            errors.append("held-out scenario count must be positive")
        if len(self.output_names) != len(self.output_units):
            errors.append("output names and units must align")
        if not self.provenance:
            errors.append("calibration provenance is required")
        return errors

    def assess(
        self,
        input_value: InputT,
        measured_residual: float,
        conservation_passed: bool,
        policy_critical: bool,
    ) -> EscalationEvidence:
        latent = self.latent_model.encode(input_value)
        return EscalationEvidence(
            outside_training_support=not self.latent_model.inside_declared_support(
                input_value
            ),
            residual_too_large=measured_residual > self.residual_threshold,
            uncertainty_too_large=(
                self.latent_model.uncertainty(latent) > self.uncertainty_threshold
            ),
            conservation_failed=not conservation_passed,
            policy_critical=policy_critical,
        )
