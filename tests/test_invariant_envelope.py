from les.contracts import InvariantEnvelope, ModuleContract
from les_state_reduction import compare_projected_trajectory


def test_invariant_envelope_collects_first_failure_witness() -> None:
    envelope = InvariantEnvelope.from_iterables(
        name="les.fast_runner.admissible",
        lane="validation",
        invariants=[
            ("nonnegative_n", lambda state: state["n"] >= 0.0),
            ("bounded_c", lambda state: state["c"] <= 3.0),
        ],
    )

    failures = envelope.collect_counterexamples({"n": -1.0, "c": 5.0})

    assert [failure.predicate for failure in failures] == [
        "nonnegative_n",
        "bounded_c",
    ]
    assert (
        envelope.first_counterexample({"n": -1.0, "c": 5.0}).predicate
        == "nonnegative_n"
    )
    assert envelope.is_admissible({"n": 1.0, "c": 2.0}) is True
    assert envelope.is_admissible({"n": -1.0, "c": 2.0}) is False


def test_module_contract_derives_invariant_envelope() -> None:
    contract = ModuleContract.from_iterables(
        name="les.modules.pumps.recirculation",
        lane="validation",
        invariants=[
            ("nonnegative_flow", lambda state: state["flow_volume"] >= 0.0),
        ],
    )

    envelope = contract.to_invariant_envelope()
    failure = envelope.first_counterexample({"flow_volume": -1.0})

    assert envelope.name == contract.name
    assert envelope.lane == contract.lane
    assert failure is not None
    assert failure.subject == contract.name
    assert failure.predicate == "nonnegative_flow"
    assert failure.witness["flow_volume"] == -1.0


def test_compare_projected_trajectory_uses_envelope_counterexample() -> None:
    envelope = InvariantEnvelope.from_iterables(
        name="les.fast_runner.admissible",
        lane="validation",
        invariants=[
            ("soil_floor", lambda state: state["n"] >= 2.0),
        ],
    )

    summary = compare_projected_trajectory(
        detailed_states=[{"n": 2.0, "c": 2.0, "s": 2.0}],
        reduced_states=[{"n": 1.0, "c": 2.0, "s": 2.0}],
        envelope=envelope,
        l1_tolerance=0.5,
    )

    assert summary.first_witness is not None
    assert summary.first_witness.counterexample is not None
    assert summary.first_witness.counterexample.subject == envelope.name
    assert summary.first_witness.counterexample.predicate == "soil_floor"
    assert summary.first_witness.failing_invariants == ("soil_floor",)
