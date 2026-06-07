"""State registry for LES."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .contracts import VariableSpec


class StateRegistry:
    """Dictionary-backed registry with optional schema metadata."""

    def __init__(self) -> None:
        self._state: Dict[str, Any] = {}
        self._specs: Dict[str, VariableSpec] = {}

    def register(
        self,
        key: str,
        value: Any = None,
        *,
        spec: Optional[VariableSpec] = None,
    ) -> None:
        """Register a new state variable, optionally with schema metadata."""
        if spec is not None:
            if spec.key != key:
                raise ValueError(f"VariableSpec key {spec.key!r} does not match {key!r}")
            self._validate_value(key, value, spec)
            self._specs[key] = spec
        self._state[key] = value

    def register_spec(self, spec: VariableSpec) -> None:
        """Attach or replace schema metadata for an existing variable key."""
        if spec.key not in self._state:
            raise KeyError(f"Variable {spec.key!r} is not registered")
        self._validate_value(spec.key, self._state[spec.key], spec)
        self._specs[spec.key] = spec

    def set(self, key: str, value: Any) -> None:
        if key not in self._state:
            raise KeyError(f"Variable {key!r} is not registered")
        spec = self._specs.get(key)
        self._validate_value(key, value, spec)
        self._state[key] = value

    def get(self, key: str) -> Any:
        if key not in self._state:
            raise KeyError(f"Variable {key!r} is not registered")
        return self._state[key]

    def get_spec(self, key: str) -> Optional[VariableSpec]:
        """Return schema metadata for a registered key, if available."""
        if key not in self._state:
            raise KeyError(f"Variable {key!r} is not registered")
        return self._specs.get(key)

    def metadata(self, key: str) -> Dict[str, Any]:
        """Return normalized metadata for a registered key."""
        if key not in self._state:
            raise KeyError(f"Variable {key!r} is not registered")
        spec = self._specs.get(key)
        if spec is None:
            return {"key": key, "registered": True, "has_spec": False}
        return {
            "key": key,
            "registered": True,
            "has_spec": True,
            "value_type": spec.value_type,
            "unit": spec.unit,
            "description": spec.description,
            "minimum": spec.minimum,
            "maximum": spec.maximum,
            "allowed_values": spec.allowed_values,
            "required": spec.required,
            "lane": spec.lane,
            "validator_count": len(spec.validators),
        }

    def keys(self) -> tuple[str, ...]:
        """Return all registered variable keys."""
        return tuple(self._state.keys())

    def validate_all(self) -> Dict[str, tuple[str, ...]]:
        """Validate all values that have an attached spec."""
        failures: Dict[str, tuple[str, ...]] = {}
        for key, spec in self._specs.items():
            errors = spec.validate(self._state.get(key))
            if errors:
                failures[key] = tuple(errors)
        return failures

    def _validate_value(
        self,
        key: str,
        value: Any,
        spec: Optional[VariableSpec],
    ) -> None:
        if spec is None:
            return
        errors = spec.validate(value)
        if errors:
            joined = "; ".join(errors)
            raise ValueError(f"Invalid value for {key!r}: {joined}")


# Global registry instance
state = StateRegistry()
state.register(
    "aq.nitrate",
    spec=VariableSpec(
        key="aq.nitrate",
        value_type=(int, float),
        unit="mg/L",
        minimum=0.0,
        lane="canonical",
        description="Measured nitrate concentration in aquaponic loop.",
    ),
)
state.register(
    "aq.orp",
    spec=VariableSpec(
        key="aq.orp",
        value_type=(int, float),
        unit="mV",
        minimum=0.0,
        maximum=1000.0,
        lane="canonical",
        description="Measured oxidation-reduction potential.",
    ),
)
