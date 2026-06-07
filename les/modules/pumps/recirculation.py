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


class PumpInvariantError(ValueError):
    """Raised when pump configuration or runtime invariants are violated."""

    def __init__(self, message: str, *, witness: Dict[str, Any]) -> None:
        super().__init__(message)
        self.witness = witness


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
        self._validate_configuration()
        self._ensure_state()
        self._adjust_runtime()

    # ------------------------------------------------------------------
    # internal helpers
    def _raise_invariant(
        self, message: str, *, context: Dict[str, Any] | None = None
    ) -> None:
        witness: Dict[str, Any] = {
            "flow_rate": self.flow_rate,
            "var_key": self.var_key,
            "lower_threshold": self.lower_threshold,
            "upper_threshold": self.upper_threshold,
            "cycle_duration": self.cycle_duration,
            "time_in_cycle": self.time_in_cycle,
            "pump_on_time": self.pump_on_time,
            "is_on": self.is_on,
            "total_volume": self.total_volume,
        }
        if context:
            witness.update(context)
        raise PumpInvariantError(message, witness=witness)

    def _validate_configuration(self) -> None:
        if self.flow_rate < 0.0:
            self._raise_invariant(
                "flow_rate must be nonnegative",
                context={"invariant": "nonnegative_flow_rate"},
            )
        if self.cycle_duration <= 0.0:
            self._raise_invariant(
                "cycle_duration must be strictly positive",
                context={"invariant": "positive_cycle_duration"},
            )
        if self.lower_threshold > self.upper_threshold:
            self._raise_invariant(
                "lower_threshold must be less than or equal to upper_threshold",
                context={"invariant": "ordered_thresholds"},
            )

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
        if not 0.0 <= self.pump_on_time <= self.cycle_duration:
            self._raise_invariant(
                "pump_on_time must stay within cycle bounds",
                context={
                    "invariant": "runtime_within_cycle_bounds",
                    "read_value": value,
                    "derived_ratio": ratio,
                },
            )

    # ------------------------------------------------------------------
    def update(self, dt: float) -> float:
        """Advance the pump simulation by ``dt`` seconds.

        Returns
        -------
        float
            Estimated volume of water moved during the update.
        """
        if dt < 0.0:
            self._raise_invariant(
                "dt must be nonnegative",
                context={"invariant": "nonnegative_dt", "dt": dt},
            )

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
