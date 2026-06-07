import pytest

from les.simulators import (
    DetailedRecirculationConfig,
    DetailedRecirculationControl,
    DetailedRecirculationState,
    DetailedRecirculationSimulator,
)


def test_detailed_sim_is_deterministic_for_same_controls() -> None:
    controls = [
        DetailedRecirculationControl(
            pump_duty=0.7,
            ammonia_input_mg_s=12.0,
            nitrate_dose_mg_s=4.0,
            plant_uptake_mg_s=5.0,
            aeration_duty=0.9,
        )
        for _ in range(20)
    ]
    sim_a = DetailedRecirculationSimulator()
    sim_b = DetailedRecirculationSimulator()

    out_a = sim_a.run(controls, include_initial=True)
    out_b = sim_b.run(controls, include_initial=True)

    assert out_a == out_b
    assert out_a[-1].time_s == pytest.approx(10.0)


def test_detailed_sim_exposes_richer_state_and_accumulators() -> None:
    cfg = DetailedRecirculationConfig(dt_s=0.25, pump_max_flow_l_s=3.0)
    sim = DetailedRecirculationSimulator(config=cfg)

    control = DetailedRecirculationControl(
        pump_duty=1.0,
        ammonia_input_mg_s=20.0,
        nitrate_dose_mg_s=10.0,
        plant_uptake_mg_s=6.0,
        aeration_duty=1.0,
    )
    for _ in range(8):
        sim.step(control)

    st = sim.state
    snapshot = sim.snapshot()

    assert st.time_s == pytest.approx(2.0)
    assert st.cumulative_recirculated_l == pytest.approx(6.0)
    assert st.cumulative_ammonia_input_mg == pytest.approx(40.0)
    assert st.cumulative_nitrate_dosed_mg == pytest.approx(20.0)
    assert st.cumulative_uptake_mg == pytest.approx(12.0)
    assert st.cumulative_nitrified_mg > 0.0
    assert st.filter_nitrate_mg_l > 7.0
    assert st.filter_ammonia_mg_l < 0.55

    expected_keys = {
        "time_s",
        "tank_ammonia_mg_l",
        "filter_ammonia_mg_l",
        "tank_nitrate_mg_l",
        "filter_nitrate_mg_l",
        "tank_do_mg_l",
        "filter_do_mg_l",
        "pump_flow_l_s",
        "cumulative_recirculated_l",
        "cumulative_ammonia_input_mg",
        "cumulative_nitrate_dosed_mg",
        "cumulative_uptake_mg",
        "cumulative_nitrified_mg",
    }
    assert set(snapshot.keys()) == expected_keys


def test_detailed_sim_aeration_control_changes_nitrification() -> None:
    cfg = DetailedRecirculationConfig(dt_s=0.5)
    oxygen_limited = DetailedRecirculationState(
        tank_do_mg_l=0.8,
        filter_do_mg_l=0.2,
        tank_ammonia_mg_l=1.1,
        filter_ammonia_mg_l=1.3,
    )
    controls_off = [
        DetailedRecirculationControl(
            pump_duty=1.0,
            ammonia_input_mg_s=14.0,
            plant_uptake_mg_s=0.0,
            aeration_duty=0.0,
        )
        for _ in range(30)
    ]
    controls_on = [
        DetailedRecirculationControl(
            pump_duty=1.0,
            ammonia_input_mg_s=14.0,
            plant_uptake_mg_s=0.0,
            aeration_duty=1.0,
        )
        for _ in range(30)
    ]

    sim_off = DetailedRecirculationSimulator(config=cfg, initial_state=oxygen_limited)
    sim_on = DetailedRecirculationSimulator(config=cfg, initial_state=oxygen_limited)
    sim_off.run(controls_off)
    sim_on.run(controls_on)

    assert sim_on.state.cumulative_nitrified_mg > sim_off.state.cumulative_nitrified_mg
    assert sim_on.state.filter_do_mg_l > sim_off.state.filter_do_mg_l


def test_detailed_sim_rejects_invalid_control_values() -> None:
    sim = DetailedRecirculationSimulator()

    with pytest.raises(ValueError, match="pump_duty"):
        sim.step(DetailedRecirculationControl(pump_duty=1.2))

    with pytest.raises(ValueError, match="ammonia_input_mg_s"):
        sim.step(DetailedRecirculationControl(pump_duty=0.2, ammonia_input_mg_s=-1.0))
