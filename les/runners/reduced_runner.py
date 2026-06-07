"""Coarse reduced runner for control/search/planning loops."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ReducedState:
    """Compact state used by reduced simulation loops."""

    subsystem: str
    process_level: float
    actuator_level: float
    step_index: int = 0
    elapsed_seconds: float = 0.0

    def as_projection(self) -> dict[str, float]:
        """Expose a projection shape for reduced-vs-detailed comparison."""
        return {
            "process_level": self.process_level,
            "actuator_level": self.actuator_level,
            "step_index": float(self.step_index),
            "elapsed_seconds": self.elapsed_seconds,
        }


@dataclass(frozen=True)
class ReducedRunnerConfig:
    """Linear coarse dynamics for a reduced subsystem model."""

    default_dt_seconds: float = 1.0
    actuator_response: float = 0.8
    passive_decay: float = 0.25
    process_bias: float = 0.0
    process_min: float = 0.0
    process_max: float = 10.0
    actuator_min: float = 0.0
    actuator_max: float = 1.0

    def __post_init__(self) -> None:
        if self.default_dt_seconds <= 0.0:
            raise ValueError("default_dt_seconds must be strictly positive")
        if self.process_min > self.process_max:
            raise ValueError("process_min must be <= process_max")
        if self.actuator_min > self.actuator_max:
            raise ValueError("actuator_min must be <= actuator_max")


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def step_reduced_state(
    state: ReducedState,
    *,
    control_input: float,
    dt_seconds: float,
    config: ReducedRunnerConfig,
) -> ReducedState:
    """Advance a reduced state by one deterministic integration step."""
    if dt_seconds <= 0.0:
        raise ValueError("dt_seconds must be strictly positive")

    actuator_level = _clamp(control_input, config.actuator_min, config.actuator_max)
    d_process = (
        config.actuator_response * actuator_level
        - config.passive_decay * state.process_level
        + config.process_bias
    )
    process_level = _clamp(
        state.process_level + (d_process * dt_seconds),
        config.process_min,
        config.process_max,
    )
    return ReducedState(
        subsystem=state.subsystem,
        process_level=process_level,
        actuator_level=actuator_level,
        step_index=state.step_index + 1,
        elapsed_seconds=state.elapsed_seconds + dt_seconds,
    )


@dataclass
class ReducedRunner:
    """Small API over reduced state stepping."""

    state: ReducedState
    config: ReducedRunnerConfig = ReducedRunnerConfig()

    @classmethod
    def from_projected_state(
        cls,
        projected: Mapping[str, float | int],
        *,
        subsystem: str = "generic",
        config: ReducedRunnerConfig | None = None,
    ) -> "ReducedRunner":
        """Build a runner from a reduced-compatible projected state."""
        return cls(
            state=ReducedState(
                subsystem=subsystem,
                process_level=float(projected.get("process_level", 0.0)),
                actuator_level=float(projected.get("actuator_level", 0.0)),
                step_index=int(projected.get("step_index", 0)),
                elapsed_seconds=float(projected.get("elapsed_seconds", 0.0)),
            ),
            config=config or ReducedRunnerConfig(),
        )

    def step(self, *, control_input: float, dt_seconds: float | None = None) -> ReducedState:
        """Apply one coarse step and store the next state."""
        step_dt = self.config.default_dt_seconds if dt_seconds is None else dt_seconds
        self.state = step_reduced_state(
            self.state,
            control_input=control_input,
            dt_seconds=step_dt,
            config=self.config,
        )
        return self.state
