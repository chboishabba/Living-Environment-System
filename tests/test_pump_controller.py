import pytest

from les.modules.pumps import PumpController
from les.modules.pumps.recirculation import PumpInvariantError


def test_pump_controller_updates_state():
    state = {"sensors": {"quality": 5.0}}
    controller = PumpController(
        state,
        flow_rate=2.0,  # volume units per second
        var_key="sensors.quality",
        lower_threshold=0.0,
        upper_threshold=10.0,
        cycle_duration=10.0,
    )

    volume = controller.update(1.0)
    assert volume == 2.0
    recirc = state["pumps"]["recirculation"]
    assert recirc["is_on"] is True
    assert recirc["flow_volume"] == 2.0
    assert recirc["total_volume"] == 2.0

    # advancing past the on-time disables the pump
    controller.update(5.0)
    recirc = state["pumps"]["recirculation"]
    assert recirc["is_on"] is False
    assert recirc["total_volume"] == 2.0


def test_pump_controller_rejects_misordered_thresholds_with_witness():
    state = {"sensors": {"quality": 5.0}}
    with pytest.raises(PumpInvariantError) as exc:
        PumpController(
            state,
            flow_rate=2.0,
            var_key="sensors.quality",
            lower_threshold=10.0,
            upper_threshold=2.0,
            cycle_duration=10.0,
        )

    err = exc.value
    assert "lower_threshold" in str(err)
    assert err.witness["invariant"] == "ordered_thresholds"
    assert err.witness["lower_threshold"] == 10.0
    assert err.witness["upper_threshold"] == 2.0


def test_pump_controller_rejects_nonpositive_cycle_duration():
    state = {"sensors": {"quality": 5.0}}
    with pytest.raises(PumpInvariantError) as exc:
        PumpController(
            state,
            flow_rate=2.0,
            var_key="sensors.quality",
            lower_threshold=0.0,
            upper_threshold=10.0,
            cycle_duration=0.0,
        )

    assert exc.value.witness["invariant"] == "positive_cycle_duration"
    assert exc.value.witness["cycle_duration"] == 0.0


def test_pump_controller_update_rejects_negative_dt_with_witness():
    state = {"sensors": {"quality": 5.0}}
    controller = PumpController(
        state,
        flow_rate=2.0,
        var_key="sensors.quality",
        lower_threshold=0.0,
        upper_threshold=10.0,
        cycle_duration=10.0,
    )

    with pytest.raises(PumpInvariantError) as exc:
        controller.update(-1.0)

    err = exc.value
    assert err.witness["invariant"] == "nonnegative_dt"
    assert err.witness["dt"] == -1.0
