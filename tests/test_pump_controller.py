from les.modules.pumps import PumpController


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
