"""Pump recirculation controller.

This module models a simple on/off pump operating on cycles. The pump
runtime within each cycle is determined by a water-quality variable
read from the global LES state. During updates the controller estimates
water flow produced by the pump and records metrics for downstream
analysis.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class PumpController:
    """Control a recirculation pump based on water-quality variables.

    Parameters
    ----------
    state:
        Shared LES state dictionary used for communication between
        modules.
    flow_rate:
        Pump flow rate in volume units per second.
    var_key:
        Dot separated key pointing to the water-quality variable inside
        ``state``. For example ``"sensors.dissolved_oxygen"``.
    lower_threshold:
        Pump remains off when the variable is below this value.
    upper_threshold:
        Pump runs for the entire cycle when the variable is above this
        value. Between the two thresholds the runtime is scaled
        linearly.
    cycle_duration:
        Duration in seconds of a single pump cycle.
    """

    state: Dict[str, Any]
    flow_rate: float
    var_key: str
    lower_threshold: float
    upper_threshold: float
    cycle_duration: float = 60.0
    time_in_cycle: float = 0.0
    pump_on_time: float = 0.0
    is_on: bool = False
    total_volume: float = 0.0

    def __post_init__(self) -> None:
        self._ensure_state()
        self._adjust_runtime()

    # ------------------------------------------------------------------
    # internal helpers
    def _ensure_state(self) -> None:
        pumps = self.state.setdefault("pumps", {})
        pumps.setdefault(
            "recirculation",
            {"is_on": self.is_on, "flow_volume": 0.0, "total_volume": 0.0},
        )

    def _read_variable(self) -> float | None:
        data: Any = self.state
        try:
            for key in self.var_key.split("."):
                data = data[key]
            return float(data)
        except (KeyError, TypeError, ValueError):
            return None

    def _adjust_runtime(self) -> None:
        value = self._read_variable()
        if value is None:
            self.pump_on_time = 0.0
            return

        if value >= self.upper_threshold:
            ratio = 1.0
        elif value <= self.lower_threshold:
            ratio = 0.0
        else:
            ratio = (value - self.lower_threshold) / (
                self.upper_threshold - self.lower_threshold
            )
        self.pump_on_time = ratio * self.cycle_duration

    # ------------------------------------------------------------------
    def update(self, dt: float) -> float:
        """Advance the pump simulation by ``dt`` seconds.

        Returns
        -------
        float
            Estimated volume of water moved during the update.
        """

        self.time_in_cycle += dt
        if self.time_in_cycle >= self.cycle_duration:
            self.time_in_cycle %= self.cycle_duration
            self._adjust_runtime()

        self.is_on = self.time_in_cycle < self.pump_on_time
        flow_volume = self.flow_rate * dt if self.is_on else 0.0
        self.total_volume += flow_volume

        recirc = self.state["pumps"]["recirculation"]
        recirc["is_on"] = self.is_on
        recirc["flow_volume"] = flow_volume
        recirc["total_volume"] = self.total_volume

        return flow_volume
