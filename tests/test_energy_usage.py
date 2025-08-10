import pytest

from les.aq import Aquarium
from les.modules.energy.usage import update_energy_usage


def test_energy_usage_accumulates():
    aq = Aquarium(pump_w=100, aerator_w=50)

    # Both devices active for one hour
    aq.pump_on = True
    aq.aerator_on = True
    update_energy_usage(aq, 1.0)
    assert aq.energy_kwh == pytest.approx((100 + 50) / 1000.0)

    # Only pump active for two more hours
    aq.aerator_on = False
    update_energy_usage(aq, 2.0)
    expected = (100 + 50) / 1000.0 + 100 * 2.0 / 1000.0
    assert aq.energy_kwh == pytest.approx(expected)
