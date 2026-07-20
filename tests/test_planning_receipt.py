from les.contracts.planning_receipt import (
    Artifact,
    ArtifactKind,
    ConservationBalance,
    EscalationEvidence,
    EvaluatedPlan,
    ModelLane,
    ObjectiveScore,
    PlanningRuntimeReceipt,
    dominates,
    pareto_front,
)


def _score(objective_id: str, direction: str, value: float, unit: str) -> ObjectiveScore:
    return ObjectiveScore(
        objective_id=objective_id,
        direction=direction,
        value=value,
        unit=unit,
        evidence_reference="fixture",
    )


def test_pareto_front_respects_direction_and_constraints() -> None:
    combined = EvaluatedPlan(
        plan_id="combined",
        hard_constraints_satisfied=True,
        objectives=(
            _score("nutrient-load", "minimise", 4.0, "kg-P/year"),
            _score("habitat", "maximise", 8.0, "index"),
        ),
    )
    mechanical = EvaluatedPlan(
        plan_id="mechanical-only",
        hard_constraints_satisfied=True,
        objectives=(
            _score("nutrient-load", "minimise", 7.0, "kg-P/year"),
            _score("habitat", "maximise", 2.0, "index"),
        ),
    )
    infeasible = EvaluatedPlan(
        plan_id="infeasible",
        hard_constraints_satisfied=False,
        objectives=(
            _score("nutrient-load", "minimise", 0.0, "kg-P/year"),
            _score("habitat", "maximise", 99.0, "index"),
        ),
    )

    assert dominates(combined, mechanical)
    assert not dominates(infeasible, combined)
    assert pareto_front((combined, mechanical, infeasible)) == (combined,)


def test_policy_critical_receipt_escalates_latent_to_authoritative() -> None:
    receipt = PlanningRuntimeReceipt(
        scenario_id="springfield-pond-fixture",
        starting_lane=ModelLane.LATENT,
        resulting_lane=ModelLane.AUTHORITATIVE,
        escalation=EscalationEvidence(policy_critical=True),
        artifacts=(
            Artifact(
                artifact_id="catchment",
                kind=ArtifactKind.VECTOR,
                uri="fixture://catchment",
                content_hash="sha256:fixture",
                producer_version="test",
                crs="EPSG:7856",
                provenance=("synthetic fixture",),
            ),
        ),
        conservation=(
            ConservationBalance(
                unit="kg-P",
                opening_storage=0.0,
                external_input=0.0,
                external_export=0.0,
                closing_storage=0.0,
                accounted_transformation=0.0,
                unaccounted_residual=0.0,
                residual_tolerance=0.0,
                model_reference="fixture",
            ),
        ),
        candidate_plans=(
            EvaluatedPlan(
                plan_id="combined",
                hard_constraints_satisfied=True,
                objectives=(_score("nutrient-load", "minimise", 4.0, "kg-P/year"),),
            ),
        ),
        selected_plan_id="combined",
        human_approval_required=True,
        deployment_permitted=False,
        provenance=("DASHI planning boundary fixture",),
    )

    assert receipt.validate() == []


def test_receipt_rejects_unverified_deployment() -> None:
    receipt = PlanningRuntimeReceipt(
        scenario_id="bad",
        starting_lane=ModelLane.SCREENING,
        resulting_lane=ModelLane.SCREENING,
        escalation=EscalationEvidence(),
        artifacts=(),
        conservation=(),
        candidate_plans=(
            EvaluatedPlan(
                plan_id="plan",
                hard_constraints_satisfied=True,
                objectives=(),
            ),
        ),
        selected_plan_id="plan",
        human_approval_required=True,
        deployment_permitted=True,
        provenance=("fixture",),
    )

    errors = receipt.validate()
    assert "deployment cannot be permitted while human approval is pending" in errors
    assert "deployment requires authoritative Path C verification" in errors
