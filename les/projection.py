"""Public helpers for projection contracts."""
from __future__ import annotations

from typing import Any, Mapping

from .contracts_projection import (
    ProjectionContract,
    ProjectionFn,
    ProjectionSummaryStatistic,
)


def project_state(
    contract: ProjectionContract,
    full_state: Mapping[str, Any],
) -> dict[str, Any]:
    """Project a full state through a contract."""
    return contract.project_state(full_state)


def summarize_projection(
    contract: ProjectionContract,
    full_state: Mapping[str, Any],
) -> dict[str, Any]:
    """Compute the contract's summary statistics for a full state."""
    return contract.summarize(full_state)
