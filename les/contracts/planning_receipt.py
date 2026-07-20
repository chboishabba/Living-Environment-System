"""Runtime-side mirror of the DASHI LES planning receipt boundary.

The Agda repository owns the semantic contract and promotion gates.  This
module provides a dependency-free Python representation for serialising GIS,
model, calibration, conservation, optimisation, and approval evidence.

It intentionally does not certify that referenced artifacts are scientifically
valid.  It verifies structural completeness and fail-closed escalation rules.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping


class ModelLane(str, Enum):
    SCREENING = "pathA-screening"
    LATENT = "pathB-latent"
    AUTHORITATIVE = "pathC-authoritative"


class ArtifactKind(str, Enum):
    RASTER = "raster-layer"
    VECTOR = "vector-layer"
    GRAPH = "graph-layer"
    TIME_SERIES = "time-series"
    MODEL_RUN = "model-run-manifest"
    SURROGATE = "surrogate-artifact"
    POPULATION = "optimisation-population"
    REPORT = "report-artifact"


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    kind: ArtifactKind
    uri: str
    content_hash: str
    producer_version: str
    crs: str = ""
    units: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.artifact_id:
            errors.append("artifact_id is required")
        if not self.uri:
            errors.append(f"{self.artifact_id}: uri is required")
        if not self.content_hash:
            errors.append(f"{self.artifact_id}: content_hash is required")
        if not self.producer_version:
            errors.append(f"{self.artifact_id}: producer_version is required")
        return errors


@dataclass(frozen=True)
class EscalationEvidence:
    outside_training_support: bool = False
    residual_too_large: bool = False
    uncertainty_too_large: bool = False
    conservation_failed: bool = False
    policy_critical: bool = False

    @property
    def requires_escalation(self) -> bool:
        return any(asdict(self).values())


@dataclass(frozen=True)
class ConservationBalance:
    unit: str
    opening_storage: float
    external_input: float
    external_export: float
    closing_storage: float
    accounted_transformation: float
    unaccounted_residual: float
    residual_tolerance: float
    model_reference: str
    evidence: tuple[str, ...] = ()

    @property
    def lhs(self) -> float:
        return self.opening_storage + self.external_input

    @property
    def rhs(self) -> float:
        return (
            self.external_export
            + self.closing_storage
            + self.accounted_transformation
            + self.unaccounted_residual
        )

    def validate(self, numerical_tolerance: float = 1e-9) -> list[str]:
        errors: list[str] = []
        if not self.unit:
            errors.append("conservation unit is required")
        if abs(self.lhs - self.rhs) > numerical_tolerance:
            errors.append(
                f"{self.unit}: balance mismatch lhs={self.lhs} rhs={self.rhs}"
            )
        if abs(self.unaccounted_residual) > self.residual_tolerance:
            errors.append(
                f"{self.unit}: residual {self.unaccounted_residual} exceeds "
                f"tolerance {self.residual_tolerance}"
            )
        if not self.model_reference:
            errors.append(f"{self.unit}: model_reference is required")
        return errors


@dataclass(frozen=True)
class ObjectiveScore:
    objective_id: str
    direction: str
    value: float
    unit: str
    evidence_reference: str

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.direction not in {"minimise", "maximise"}:
            errors.append(f"{self.objective_id}: invalid direction")
        if not self.unit:
            errors.append(f"{self.objective_id}: unit is required")
        if not self.evidence_reference:
            errors.append(f"{self.objective_id}: evidence reference is required")
        return errors


@dataclass(frozen=True)
class EvaluatedPlan:
    plan_id: str
    hard_constraints_satisfied: bool
    objectives: tuple[ObjectiveScore, ...]
    intervention_artifacts: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = ()

    def validate(self) -> list[str]:
        errors = [e for objective in self.objectives for e in objective.validate()]
        ids = [objective.objective_id for objective in self.objectives]
        if len(ids) != len(set(ids)):
            errors.append(f"{self.plan_id}: duplicate objective ids")
        if not self.plan_id:
            errors.append("plan_id is required")
        return errors


def dominates(better: EvaluatedPlan, worse: EvaluatedPlan) -> bool:
    """Return finite Pareto dominance for aligned objective vectors."""

    if not (better.hard_constraints_satisfied and worse.hard_constraints_satisfied):
        return False
    better_by_id = {score.objective_id: score for score in better.objectives}
    worse_by_id = {score.objective_id: score for score in worse.objectives}
    if better_by_id.keys() != worse_by_id.keys():
        return False

    no_worse = True
    strictly_better = False
    for objective_id, a in better_by_id.items():
        b = worse_by_id[objective_id]
        if a.direction != b.direction or a.unit != b.unit:
            return False
        if a.direction == "minimise":
            no_worse &= a.value <= b.value
            strictly_better |= a.value < b.value
        else:
            no_worse &= a.value >= b.value
            strictly_better |= a.value > b.value
    return no_worse and strictly_better


def pareto_front(plans: Iterable[EvaluatedPlan]) -> tuple[EvaluatedPlan, ...]:
    population = tuple(plans)
    return tuple(
        candidate
        for candidate in population
        if candidate.hard_constraints_satisfied
        and not any(
            other is not candidate and dominates(other, candidate)
            for other in population
        )
    )


@dataclass(frozen=True)
class PlanningRuntimeReceipt:
    scenario_id: str
    starting_lane: ModelLane
    resulting_lane: ModelLane
    escalation: EscalationEvidence
    artifacts: tuple[Artifact, ...]
    conservation: tuple[ConservationBalance, ...]
    candidate_plans: tuple[EvaluatedPlan, ...]
    selected_plan_id: str
    source_hypotheses: tuple[Mapping[str, Any], ...] = ()
    community_constraints: tuple[Mapping[str, Any], ...] = ()
    human_approval_required: bool = True
    deployment_permitted: bool = False
    provenance: tuple[str, ...] = ()

    def validate(self) -> list[str]:
        errors: list[str] = []
        errors.extend(e for artifact in self.artifacts for e in artifact.validate())
        errors.extend(e for balance in self.conservation for e in balance.validate())
        errors.extend(e for plan in self.candidate_plans for e in plan.validate())

        plan_ids = {plan.plan_id for plan in self.candidate_plans}
        if self.selected_plan_id not in plan_ids:
            errors.append("selected_plan_id is not in candidate_plans")

        expected_lane = self.starting_lane
        if self.escalation.requires_escalation:
            expected_lane = {
                ModelLane.SCREENING: ModelLane.LATENT,
                ModelLane.LATENT: ModelLane.AUTHORITATIVE,
                ModelLane.AUTHORITATIVE: ModelLane.AUTHORITATIVE,
            }[self.starting_lane]
        if self.resulting_lane != expected_lane:
            errors.append(
                f"resulting lane {self.resulting_lane.value} does not match "
                f"fail-closed lane {expected_lane.value}"
            )

        if self.deployment_permitted and self.human_approval_required:
            errors.append("deployment cannot be permitted while human approval is pending")
        if self.deployment_permitted and self.resulting_lane is not ModelLane.AUTHORITATIVE:
            errors.append("deployment requires authoritative Path C verification")
        if not self.provenance:
            errors.append("receipt provenance is required")
        return errors

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["starting_lane"] = self.starting_lane.value
        data["resulting_lane"] = self.resulting_lane.value
        for artifact in data["artifacts"]:
            artifact["kind"] = artifact["kind"].value
        return data
