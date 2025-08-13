from les_core import (
    simulate,
    water_ph,
    dissolved_oxygen,
    simulation_steps_total,
    simulation_throughput,
)


def test_simulate_updates_metrics():
    initial_ph = water_ph._value.get()
    initial_oxygen = dissolved_oxygen._value.get()
    initial_steps = simulation_steps_total._value.get()
    initial_throughput = simulation_throughput._value.get()

    simulate(iterations=2, delay=0)

    assert water_ph._value.get() != initial_ph
    assert dissolved_oxygen._value.get() != initial_oxygen
    assert simulation_steps_total._value.get() > initial_steps
    assert simulation_throughput._value.get() != initial_throughput
