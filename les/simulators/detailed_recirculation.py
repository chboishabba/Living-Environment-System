"""Detailed recirculation simulator for a tiny nutrient-loop subsystem.

This model intentionally keeps a narrow scope while exposing richer internal
state than reduced-order runners. It represents two connected compartments:
an aquarium tank and a biofilter loop with explicit pump control.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Iterable


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


@dataclass(frozen=True)
class DetailedRecirculationControl:
    """Control input for one simulator time step.

    All mass-flow rates are in mg/s.
    """

    pump_duty: float
    ammonia_input_mg_s: float = 0.0
    nitrate_dose_mg_s: float = 0.0
    plant_uptake_mg_s: float = 0.0
    aeration_duty: float = 1.0

    def validate(self) -> None:
        if not 0.0 <= self.pump_duty <= 1.0:
            raise ValueError("pump_duty must be in [0, 1]")
        if not 0.0 <= self.aeration_duty <= 1.0:
            raise ValueError("aeration_duty must be in [0, 1]")
        if self.ammonia_input_mg_s < 0.0:
            raise ValueError("ammonia_input_mg_s must be nonnegative")
        if self.nitrate_dose_mg_s < 0.0:
            raise ValueError("nitrate_dose_mg_s must be nonnegative")
        if self.plant_uptake_mg_s < 0.0:
            raise ValueError("plant_uptake_mg_s must be nonnegative")


@dataclass(frozen=True)
class DetailedRecirculationConfig:
    """Static parameters for the detailed recirculation simulator."""

    dt_s: float = 0.5
    tank_volume_l: float = 160.0
    biofilter_volume_l: float = 40.0
    pump_max_flow_l_s: float = 2.5
    nitrification_rate_s: float = 0.012
    nitrification_o2_half_sat_mg_l: float = 3.0
    nitrification_o2_cost_mg_per_mg: float = 1.6
    gas_transfer_rate_s: float = 0.03
    do_saturation_mg_l: float = 8.5

    def __post_init__(self) -> None:
        positive_fields = (
            "dt_s",
            "tank_volume_l",
            "biofilter_volume_l",
            "pump_max_flow_l_s",
            "nitrification_rate_s",
            "nitrification_o2_half_sat_mg_l",
            "nitrification_o2_cost_mg_per_mg",
            "gas_transfer_rate_s",
            "do_saturation_mg_l",
        )
        for field_name in positive_fields:
            if getattr(self, field_name) <= 0.0:
                raise ValueError(f"{field_name} must be strictly positive")


@dataclass(frozen=True)
class DetailedRecirculationState:
    """Internal state exposed by the detailed recirculation surface."""

    time_s: float = 0.0
    tank_ammonia_mg_l: float = 0.35
    filter_ammonia_mg_l: float = 0.55
    tank_nitrate_mg_l: float = 9.0
    filter_nitrate_mg_l: float = 7.0
    tank_do_mg_l: float = 7.4
    filter_do_mg_l: float = 6.2
    pump_flow_l_s: float = 0.0
    cumulative_recirculated_l: float = 0.0
    cumulative_ammonia_input_mg: float = 0.0
    cumulative_nitrate_dosed_mg: float = 0.0
    cumulative_uptake_mg: float = 0.0
    cumulative_nitrified_mg: float = 0.0


class DetailedRecirculationSimulator:
    """Fine-step deterministic simulator for tank/biofilter recirculation."""

    def __init__(
        self,
        config: DetailedRecirculationConfig | None = None,
        initial_state: DetailedRecirculationState | None = None,
    ) -> None:
        self.config = config or DetailedRecirculationConfig()
        self._state = initial_state or DetailedRecirculationState()

    @property
    def state(self) -> DetailedRecirculationState:
        return replace(self._state)

    def snapshot(self) -> dict[str, float]:
        return asdict(self._state)

    def step(self, control: DetailedRecirculationControl) -> DetailedRecirculationState:
        control.validate()
        cfg = self.config
        st = self._state

        dt = cfg.dt_s
        flow_l_s = control.pump_duty * cfg.pump_max_flow_l_s
        tank_exchange = _clamp(flow_l_s * dt / cfg.tank_volume_l, 0.0, 1.0)
        filter_exchange = _clamp(flow_l_s * dt / cfg.biofilter_volume_l, 0.0, 1.0)

        tank_ammonia = st.tank_ammonia_mg_l + tank_exchange * (
            st.filter_ammonia_mg_l - st.tank_ammonia_mg_l
        )
        filter_ammonia = st.filter_ammonia_mg_l + filter_exchange * (
            st.tank_ammonia_mg_l - st.filter_ammonia_mg_l
        )

        tank_nitrate = st.tank_nitrate_mg_l + tank_exchange * (
            st.filter_nitrate_mg_l - st.tank_nitrate_mg_l
        )
        filter_nitrate = st.filter_nitrate_mg_l + filter_exchange * (
            st.tank_nitrate_mg_l - st.filter_nitrate_mg_l
        )

        tank_do = st.tank_do_mg_l + tank_exchange * (st.filter_do_mg_l - st.tank_do_mg_l)
        filter_do = st.filter_do_mg_l + filter_exchange * (st.tank_do_mg_l - st.filter_do_mg_l)

        ammonia_added_mg = control.ammonia_input_mg_s * dt
        nitrate_dosed_mg = control.nitrate_dose_mg_s * dt
        tank_ammonia += ammonia_added_mg / cfg.tank_volume_l
        tank_nitrate += nitrate_dosed_mg / cfg.tank_volume_l

        nitrate_pool_mg = max(0.0, tank_nitrate * cfg.tank_volume_l)
        uptake_mg = min(control.plant_uptake_mg_s * dt, nitrate_pool_mg)
        tank_nitrate -= uptake_mg / cfg.tank_volume_l

        oxygen_factor = _clamp(filter_do / cfg.nitrification_o2_half_sat_mg_l, 0.0, 1.0)
        nitrification_rate_mg_l_s = cfg.nitrification_rate_s * max(0.0, filter_ammonia) * oxygen_factor
        nitrified_mg = min(
            nitrification_rate_mg_l_s * dt * cfg.biofilter_volume_l,
            max(0.0, filter_ammonia * cfg.biofilter_volume_l),
        )

        filter_ammonia -= nitrified_mg / cfg.biofilter_volume_l
        filter_nitrate += nitrified_mg / cfg.biofilter_volume_l

        o2_recovery_mg_l = (
            cfg.gas_transfer_rate_s * control.aeration_duty * (cfg.do_saturation_mg_l - filter_do) * dt
        )
        o2_consumption_mg_l = (nitrified_mg * cfg.nitrification_o2_cost_mg_per_mg) / cfg.biofilter_volume_l
        filter_do = max(0.0, filter_do + o2_recovery_mg_l - o2_consumption_mg_l)

        self._state = DetailedRecirculationState(
            time_s=st.time_s + dt,
            tank_ammonia_mg_l=max(0.0, tank_ammonia),
            filter_ammonia_mg_l=max(0.0, filter_ammonia),
            tank_nitrate_mg_l=max(0.0, tank_nitrate),
            filter_nitrate_mg_l=max(0.0, filter_nitrate),
            tank_do_mg_l=max(0.0, tank_do),
            filter_do_mg_l=filter_do,
            pump_flow_l_s=flow_l_s,
            cumulative_recirculated_l=st.cumulative_recirculated_l + flow_l_s * dt,
            cumulative_ammonia_input_mg=st.cumulative_ammonia_input_mg + ammonia_added_mg,
            cumulative_nitrate_dosed_mg=st.cumulative_nitrate_dosed_mg + nitrate_dosed_mg,
            cumulative_uptake_mg=st.cumulative_uptake_mg + uptake_mg,
            cumulative_nitrified_mg=st.cumulative_nitrified_mg + nitrified_mg,
        )
        return replace(self._state)

    def run(
        self,
        controls: Iterable[DetailedRecirculationControl],
        *,
        include_initial: bool = False,
    ) -> tuple[DetailedRecirculationState, ...]:
        series: list[DetailedRecirculationState] = []
        if include_initial:
            series.append(self.state)
        for control in controls:
            series.append(self.step(control))
        return tuple(series)
