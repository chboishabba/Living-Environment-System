"""Energy usage utilities.

This module provides a helper that reads the current state of devices such as
pumps and aerators from an aquarium instance and accumulates their energy
consumption in kilowatt hours (kWh).
"""


def update_energy_usage(aq, dt_hours):
    """Update ``aq.energy_kwh`` based on device states.

    Parameters
    ----------
    aq: object
        Aquarium-like instance with ``pump_on``, ``aerator_on`` and power rating
        attributes ``pump_w`` and ``aerator_w``. ``aq.energy_kwh`` will be
        created if missing and incremented with the energy consumed during this
        timestep.
    dt_hours: float
        Duration of the simulation step in hours.
    """
    power_w = 0.0
    if getattr(aq, "pump_on", False):
        power_w += getattr(aq, "pump_w", 0.0)
    if getattr(aq, "aerator_on", False):
        power_w += getattr(aq, "aerator_w", 0.0)
    # Convert watts * hours to kilowatt hours
    energy_kwh = power_w * dt_hours / 1000.0
    aq.energy_kwh = getattr(aq, "energy_kwh", 0.0) + energy_kwh
    return aq.energy_kwh
