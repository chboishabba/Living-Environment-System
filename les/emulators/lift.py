"""Cheap reduced-state lift/emulator surface for deterministic offline use."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping, Sequence

from les_state_reduction import BucketConfig, divergence_proxy_vector

StateVector = Mapping[str, float]
ControlVector = Mapping[str, float]
CorrectionVector = Mapping[str, float]
CorrectionHook = Callable[[int, Mapping[str, float], Mapping[str, float]], CorrectionVector]


def _to_float_map(values: Mapping[str, float], defaults: Mapping[str, float] | None = None) -> dict[str, float]:
    out = {str(key): float(value) for key, value in values.items()}
    if defaults:
        for key, default_value in defaults.items():
            out.setdefault(str(key), float(default_value))
    return out


def _clip_value(value: float, lower: float | None, upper: float | None) -> float:
    if lower is not None:
        value = max(lower, value)
    if upper is not None:
        value = min(upper, value)
    return value


def reconstruct_fine_subset(
    reduced_state: StateVector,
    *,
    fields: Sequence[str] | None = None,
    bucket_configs: Mapping[str, BucketConfig] | None = None,
    scales: Mapping[str, float] | None = None,
    offsets: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """Reconstruct a cheap subset of continuous-like proxies from coarse state.

    If bucket configs are provided, integer buckets are lifted using bucket midpoints.
    Otherwise coarse numeric state values are used directly. The result is cheap and
    deterministic and intentionally low-fidelity.
    """
    fields = tuple(fields) if fields is not None else tuple(reduced_state.keys())
    scales = scales or {}
    offsets = offsets or {}

    fine: dict[str, float] = {}
    for key in fields:
        raw = float(reduced_state.get(key, 0.0))
        if bucket_configs and key in bucket_configs:
            bucket = int(raw)
            raw = bucket_configs[key].midpoint(bucket)
        scale = float(scales.get(key, 1.0))
        offset = float(offsets.get(key, 0.0))
        fine[key] = raw * scale + offset
    return fine


@dataclass(frozen=True)
class LiftEmulatorConfig:
    """Parameters for a tiny affine reduced-state emulator.

    Attributes are intentionally minimal:
    - `control_gains[state_key][control_key]`
    - optional linear leakage and drift terms
    - optional output reconstruction scales/offsets for cheap fine proxies
    """

    control_gains: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    leakage: Mapping[str, float] = field(default_factory=dict)
    drift: Mapping[str, float] = field(default_factory=dict)
    lower_bounds: Mapping[str, float] = field(default_factory=dict)
    upper_bounds: Mapping[str, float] = field(default_factory=dict)
    correction_gain: float = 1.0
    reconstruction_fields: tuple[str, ...] = ("n", "c", "s")
    bucket_configs: Mapping[str, BucketConfig] | None = None
    reconstruction_scales: Mapping[str, float] = field(default_factory=dict)
    reconstruction_offsets: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class LiftStepResult:
    """Result for a single emulator step."""

    step: int
    reduced_state: dict[str, float]
    control: dict[str, float]
    next_reduced_state: dict[str, float]
    applied_corrections: dict[str, float]
    proxy_vector: dict[str, float]
    fine_outputs: dict[str, float]


@dataclass(frozen=True)
class EmulationSummary:
    """Collection of emulator steps with proxy series surfaced for offline use."""

    steps: tuple[LiftStepResult, ...]
    initial_state: dict[str, float]

    @property
    def final_state(self) -> dict[str, float]:
        if not self.steps:
            return dict(self.initial_state)
        return dict(self.steps[-1].next_reduced_state)

    @property
    def proxy_series(self) -> tuple[dict[str, float], ...]:
        return tuple(step.proxy_vector for step in self.steps)


def emulate_reduced_step(
    reduced_state: StateVector,
    control: ControlVector,
    *,
    config: LiftEmulatorConfig,
    dt: float = 1.0,
    step: int = 0,
    correction: CorrectionVector | None = None,
    apply_correction: bool = True,
    projection_keys: Sequence[str] | None = None,
) -> LiftStepResult:
    """Advance a reduced state one cheap deterministic step.

    The model is affine in controls:
      next[x] = clamp(
          x + dt * (drift[x] + Σ control[u]*gain[x][u] - leakage[x]*x)
          + gain*correction[x]
      )
    """
    if dt <= 0.0:
        raise ValueError("dt must be positive")

    control_f = _to_float_map(control)
    base = _to_float_map(reduced_state)
    correction = _to_float_map(correction or {})
    applied_corrections: dict[str, float] = {}
    keys = tuple(sorted(config.control_gains.keys() | base.keys()))

    next_state: dict[str, float] = {}
    for key in keys:
        current = base.get(key, 0.0)
        gains = config.control_gains.get(key, {})
        control_delta = sum(value * gains.get(name, 0.0) for name, value in control_f.items())
        drift = float(config.drift.get(key, 0.0))
        leakage = float(config.leakage.get(key, 0.0))
        raw = current + dt * (drift + control_delta - leakage * current)

        correction_term = (
            config.correction_gain * float(correction.get(key, 0.0)) if apply_correction else 0.0
        )
        applied_corrections[key] = correction_term
        raw += correction_term

        next_state[key] = _clip_value(
            raw,
            config.lower_bounds.get(key),
            config.upper_bounds.get(key),
        )

    fine_outputs = reconstruct_fine_subset(
        next_state,
        fields=projection_keys or config.reconstruction_fields,
        bucket_configs=config.bucket_configs,
        scales=config.reconstruction_scales,
        offsets=config.reconstruction_offsets,
    )
    proxy_vector = divergence_proxy_vector(fine_outputs, next_state, keys=projection_keys or config.reconstruction_fields)

    return LiftStepResult(
        step=step,
        reduced_state=dict(base),
        control=control_f,
        next_reduced_state=next_state,
        applied_corrections=applied_corrections,
        proxy_vector=proxy_vector,
        fine_outputs=fine_outputs,
    )


def emulate_trajectory(
    initial_state: StateVector,
    controls: Sequence[ControlVector],
    *,
    config: LiftEmulatorConfig,
    dt: float = 1.0,
    corrections: Sequence[CorrectionVector] | None = None,
    correction_hook: CorrectionHook | None = None,
    projection_keys: Sequence[str] | None = None,
) -> EmulationSummary:
    """Simulate a short trajectory with optional correction injection.

    Provide either `corrections` (indexed sequence) or `correction_hook`.
    """
    if corrections is not None and len(corrections) != len(controls):
        raise ValueError("corrections length must match controls length")

    current = dict(_to_float_map(initial_state))
    outputs: list[LiftStepResult] = []

    for step, control in enumerate(controls):
        correction: CorrectionVector = {}
        if correction_hook is not None:
            correction = correction_hook(step, dict(current), control)
        elif corrections is not None:
            correction = corrections[step]

        result = emulate_reduced_step(
            current,
            control,
            config=config,
            dt=dt,
            step=step,
            correction=correction,
            projection_keys=projection_keys,
        )
        outputs.append(result)
        current = result.next_reduced_state

    return EmulationSummary(steps=tuple(outputs), initial_state=dict(_to_float_map(initial_state)))
