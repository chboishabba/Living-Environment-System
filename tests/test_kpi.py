import pytest

from les.aq import Aquarium
from les.kpi import energy_kpis


def test_energy_kpis_returns_expected_metrics():
    aq = Aquarium(total_fish_kg=5.0, water_volume_l=100.0)
    aq.energy_kwh = 10.0
    kpis = energy_kpis(aq)
    assert kpis["energy_per_kg_fish"] == pytest.approx(2.0)
    assert kpis["energy_per_liter_water"] == pytest.approx(0.1)


def test_energy_kpis_skips_missing_or_zero():
    class DummyAq:
        energy_kwh = 10.0
        water_volume_l = 100.0

    kpis = energy_kpis(DummyAq())
    assert "energy_per_kg_fish" not in kpis
    assert kpis["energy_per_liter_water"] == pytest.approx(0.1)

    aq = Aquarium(total_fish_kg=0.0, water_volume_l=0.0)
    aq.energy_kwh = 5.0
    kpis = energy_kpis(aq)
    assert kpis == {}
