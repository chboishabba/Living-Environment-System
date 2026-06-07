import pytest

from les.contracts import ModuleContract, VariableSpec
from les.state import StateRegistry


def test_state_registry_register_and_get():
    registry = StateRegistry()
    registry.register('foo', 1)
    assert registry.get('foo') == 1


def test_state_registry_set_updates_and_error_on_unregistered():
    registry = StateRegistry()
    registry.register('foo', 1)
    registry.set('foo', 2)
    assert registry.get('foo') == 2
    with pytest.raises(KeyError):
        registry.set('bar', 3)
    with pytest.raises(KeyError):
        registry.get('bar')


def test_state_registry_tracks_variable_specs_and_metadata():
    registry = StateRegistry()
    spec = VariableSpec(
        key="aq.nitrate",
        value_type=(int, float),
        unit="mg/L",
        minimum=0.0,
        lane="canonical",
        description="Measured nitrate concentration.",
    )

    registry.register("aq.nitrate", 10.5, spec=spec)

    assert registry.get_spec("aq.nitrate") == spec
    assert registry.metadata("aq.nitrate") == {
        "key": "aq.nitrate",
        "registered": True,
        "has_spec": True,
        "value_type": (int, float),
        "unit": "mg/L",
        "description": "Measured nitrate concentration.",
        "minimum": 0.0,
        "maximum": None,
        "allowed_values": None,
        "required": False,
        "lane": "canonical",
        "validator_count": 0,
    }


def test_state_registry_rejects_values_that_violate_spec():
    registry = StateRegistry()
    registry.register(
        "aq.orp",
        300.0,
        spec=VariableSpec(
            key="aq.orp",
            value_type=(int, float),
            minimum=0.0,
            maximum=1000.0,
        ),
    )

    with pytest.raises(ValueError, match="above maximum"):
        registry.set("aq.orp", 1500.0)


def test_module_contract_collects_counterexample_witnesses():
    contract = ModuleContract.from_iterables(
        name="les.modules.pumps.recirculation",
        lane="validation",
        requires=["sensors.quality"],
        provides=["pumps.recirculation.flow_volume"],
        invariants=[
            ("nonnegative_flow", lambda state: state["flow_volume"] >= 0.0),
            ("bounded_runtime", lambda state: state["pump_on_time"] <= state["cycle_duration"]),
        ],
    )

    failures = contract.collect_counterexamples(
        {
            "flow_volume": -1.0,
            "pump_on_time": 12.0,
            "cycle_duration": 10.0,
        }
    )

    assert [failure.predicate for failure in failures] == [
        "nonnegative_flow",
        "bounded_runtime",
    ]
    assert failures[0].subject == "les.modules.pumps.recirculation"
    assert failures[0].witness["flow_volume"] == -1.0
