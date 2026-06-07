"""Contract primitives for LES modules and state surfaces."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, List, Literal, Mapping, Optional, Tuple


ModuleLane = Literal["canonical", "experimental", "validation", "surrogate"]
Validator = Callable[[Any], bool]
Invariant = Callable[[Mapping[str, Any]], bool]


@dataclass(frozen=True)
class Counterexample:
    """Witness describing how a contract or invariant was violated."""

    subject: str
    predicate: str
    witness: Mapping[str, Any]
    message: str


@dataclass(frozen=True)
class InvariantEnvelope:
    """Named bundle of admissibility predicates for a state surface."""

    name: str
    lane: ModuleLane
    invariants: Tuple[Tuple[str, Invariant], ...] = field(default_factory=tuple)
    description: Optional[str] = None

    @classmethod
    def from_iterables(
        cls,
        *,
        name: str,
        lane: ModuleLane,
        invariants: Optional[Iterable[Tuple[str, Invariant]]] = None,
        description: Optional[str] = None,
    ) -> "InvariantEnvelope":
        """Construct an envelope while normalizing invariant iterables."""
        return cls(
            name=name,
            lane=lane,
            invariants=tuple(invariants) if invariants is not None else (),
            description=description,
        )

    @classmethod
    def from_module_contract(cls, contract: "ModuleContract") -> "InvariantEnvelope":
        """Derive an admissibility envelope from an existing module contract."""
        return cls(
            name=contract.name,
            lane=contract.lane,
            invariants=contract.invariants,
            description=contract.description,
        )

    def validate(self, state_values: Mapping[str, Any]) -> List[str]:
        """Return envelope violations for the provided state."""
        errors: List[str] = []
        for name, invariant in self.invariants:
            try:
                if not invariant(state_values):
                    errors.append(f"invariant {name!r} failed")
            except Exception as exc:  # pragma: no cover - defensive path
                errors.append(f"invariant {name!r} raised: {exc}")
        return errors

    def collect_counterexamples(
        self, state_values: Mapping[str, Any]
    ) -> List[Counterexample]:
        """Return invariant failures as witness-bearing counterexamples."""
        failures: List[Counterexample] = []
        for name, invariant in self.invariants:
            try:
                ok = invariant(state_values)
            except Exception as exc:  # pragma: no cover - defensive path
                failures.append(
                    Counterexample(
                        subject=self.name,
                        predicate=name,
                        witness=dict(state_values),
                        message=f"invariant raised: {exc}",
                    )
                )
                continue
            if not ok:
                failures.append(
                    Counterexample(
                        subject=self.name,
                        predicate=name,
                        witness=dict(state_values),
                        message=f"invariant {name!r} failed",
                    )
                )
        return failures

    def first_counterexample(
        self, state_values: Mapping[str, Any]
    ) -> Optional[Counterexample]:
        """Return the first failing invariant witness, if any."""
        failures = self.collect_counterexamples(state_values)
        return failures[0] if failures else None

    def is_admissible(self, state_values: Mapping[str, Any]) -> bool:
        """Return whether all envelope invariants hold."""
        return not self.validate(state_values)


@dataclass(frozen=True)
class VariableSpec:
    """Schema metadata and validation rules for one state variable."""

    key: str
    value_type: type[Any] | Tuple[type[Any], ...] | None = None
    unit: Optional[str] = None
    description: Optional[str] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    allowed_values: Optional[Tuple[Any, ...]] = None
    required: bool = False
    lane: ModuleLane = "canonical"
    validators: Tuple[Validator, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError(
                f"VariableSpec {self.key!r} has invalid range: minimum > maximum"
            )

    @classmethod
    def from_iterables(
        cls,
        *,
        key: str,
        value_type: type[Any] | Tuple[type[Any], ...] | None = None,
        unit: Optional[str] = None,
        description: Optional[str] = None,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        allowed_values: Optional[Iterable[Any]] = None,
        required: bool = False,
        lane: ModuleLane = "canonical",
        validators: Optional[Iterable[Validator]] = None,
    ) -> "VariableSpec":
        """Construct a spec while normalizing iterables into immutable tuples."""
        return cls(
            key=key,
            value_type=value_type,
            unit=unit,
            description=description,
            minimum=minimum,
            maximum=maximum,
            allowed_values=tuple(allowed_values) if allowed_values is not None else None,
            required=required,
            lane=lane,
            validators=tuple(validators) if validators is not None else (),
        )

    def validate(self, value: Any) -> List[str]:
        """Return validation errors for a candidate value."""
        errors: List[str] = []

        if value is None:
            if self.required:
                errors.append("value is required")
            return errors

        if self.value_type is not None and not isinstance(value, self.value_type):
            errors.append(f"expected type {self.value_type}, got {type(value)}")
            return errors

        if self.allowed_values is not None and value not in self.allowed_values:
            errors.append(f"value {value!r} is not in allowed values {self.allowed_values!r}")

        if self.minimum is not None:
            try:
                if value < self.minimum:
                    errors.append(f"value {value!r} is below minimum {self.minimum}")
            except TypeError:
                errors.append("minimum check is not applicable to value type")

        if self.maximum is not None:
            try:
                if value > self.maximum:
                    errors.append(f"value {value!r} is above maximum {self.maximum}")
            except TypeError:
                errors.append("maximum check is not applicable to value type")

        for validator in self.validators:
            try:
                ok = validator(value)
            except Exception as exc:  # pragma: no cover - defensive path
                errors.append(f"validator {validator.__name__} raised: {exc}")
                continue
            if not ok:
                errors.append(f"validator {validator.__name__} rejected value {value!r}")
        return errors


@dataclass(frozen=True)
class ModuleContract:
    """Explicit module IO and invariant contract."""

    name: str
    lane: ModuleLane
    requires: Tuple[str, ...] = field(default_factory=tuple)
    provides: Tuple[str, ...] = field(default_factory=tuple)
    invariants: Tuple[Tuple[str, Invariant], ...] = field(default_factory=tuple)
    description: Optional[str] = None

    @classmethod
    def from_iterables(
        cls,
        *,
        name: str,
        lane: ModuleLane,
        requires: Optional[Iterable[str]] = None,
        provides: Optional[Iterable[str]] = None,
        invariants: Optional[Iterable[Tuple[str, Invariant]]] = None,
        description: Optional[str] = None,
    ) -> "ModuleContract":
        return cls(
            name=name,
            lane=lane,
            requires=tuple(requires) if requires is not None else (),
            provides=tuple(provides) if provides is not None else (),
            invariants=tuple(invariants) if invariants is not None else (),
            description=description,
        )

    def missing_requirements(self, available_keys: Iterable[str]) -> List[str]:
        """Return required keys that are currently missing."""
        known = set(available_keys)
        return [key for key in self.requires if key not in known]

    def validate_invariants(self, state_values: Mapping[str, Any]) -> List[str]:
        """Return invariant violations for the provided state."""
        errors: List[str] = []
        for name, invariant in self.invariants:
            try:
                if not invariant(state_values):
                    errors.append(f"invariant {name!r} failed")
            except Exception as exc:  # pragma: no cover - defensive path
                errors.append(f"invariant {name!r} raised: {exc}")
        return errors

    def to_invariant_envelope(self) -> InvariantEnvelope:
        """Convert the contract into a named admissibility envelope."""
        return InvariantEnvelope.from_module_contract(self)

    def collect_counterexamples(
        self, state_values: Mapping[str, Any]
    ) -> List[Counterexample]:
        """Return invariant failures as witness-bearing counterexamples."""
        failures: List[Counterexample] = []
        for name, invariant in self.invariants:
            try:
                ok = invariant(state_values)
            except Exception as exc:  # pragma: no cover - defensive path
                failures.append(
                    Counterexample(
                        subject=self.name,
                        predicate=name,
                        witness=dict(state_values),
                        message=f"invariant raised: {exc}",
                    )
                )
                continue
            if not ok:
                failures.append(
                    Counterexample(
                        subject=self.name,
                        predicate=name,
                        witness=dict(state_values),
                        message=f"invariant {name!r} failed",
                    )
                )
        return failures

    def first_counterexample(
        self, state_values: Mapping[str, Any]
    ) -> Optional[Counterexample]:
        """Return the first invariant witness, if any."""
        failures = self.collect_counterexamples(state_values)
        return failures[0] if failures else None
