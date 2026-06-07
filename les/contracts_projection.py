"""Explicit contracts for projecting full state into reduced state surfaces."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Mapping


ProjectionFn = Callable[[Mapping[str, Any]], Mapping[str, Any]]
SummarySource = Literal["full_state", "reduced_state"]


@dataclass(frozen=True)
class ProjectionSummaryStatistic:
    """Metadata for a derived statistic computed alongside a projection."""

    name: str
    compute: Callable[[Mapping[str, Any]], Any]
    source: SummarySource = "reduced_state"
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ProjectionSummaryStatistic.name must not be empty")
        if self.source not in ("full_state", "reduced_state"):
            raise ValueError(f"Unsupported summary source {self.source!r}")


@dataclass(frozen=True)
class ProjectionContract:
    """Contract for a full_state -> reduced_state mapping."""

    name: str
    projection: ProjectionFn
    retained_variables: tuple[str, ...] = field(default_factory=tuple)
    discarded_variables: tuple[str, ...] = field(default_factory=tuple)
    summary_statistics: tuple[ProjectionSummaryStatistic, ...] = field(default_factory=tuple)
    description: str | None = None

    def __post_init__(self) -> None:
        overlap = set(self.retained_variables) & set(self.discarded_variables)
        if overlap:
            joined = ", ".join(sorted(overlap))
            raise ValueError(f"retained_variables and discarded_variables overlap: {joined}")

        summary_names = [stat.name for stat in self.summary_statistics]
        if len(set(summary_names)) != len(summary_names):
            raise ValueError("summary_statistics must use unique names")

    def project_state(self, full_state: Mapping[str, Any]) -> dict[str, Any]:
        """Apply the contract projection and normalize the result to a dict."""
        return dict(self.projection(full_state))

    def summarize(self, full_state: Mapping[str, Any]) -> dict[str, Any]:
        """Compute optional summary statistics for the projected surface."""
        reduced_state = self.project_state(full_state)
        summary: dict[str, Any] = {}
        for statistic in self.summary_statistics:
            source_state = full_state if statistic.source == "full_state" else reduced_state
            summary[statistic.name] = statistic.compute(source_state)
        return summary
