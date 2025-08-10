"""Threshold-based alert engine for LES."""
from __future__ import annotations
from typing import Dict, List, Tuple, Optional

from .state import StateRegistry, state


class AlertEngine:
    """Simple threshold alert engine."""

    def __init__(self) -> None:
        self._thresholds: Dict[str, Tuple[Optional[float], Optional[float]]] = {}

    def register_threshold(self, key: str, low: Optional[float] = None, high: Optional[float] = None) -> None:
        """Register acceptable range for a variable."""
        self._thresholds[key] = (low, high)

    def check(self, registry: StateRegistry = state) -> List[str]:
        """Check all thresholds and return alert messages."""
        alerts: List[str] = []
        for key, (low, high) in self._thresholds.items():
            try:
                value = registry.get(key)
            except KeyError:
                continue
            if value is None:
                continue
            if low is not None and value < low:
                alerts.append(f"{key} below threshold ({value} < {low})")
            if high is not None and value > high:
                alerts.append(f"{key} above threshold ({value} > {high})")
        return alerts


# Global alert engine instance with default thresholds
alert_engine = AlertEngine()
alert_engine.register_threshold("aq.nitrate", low=0.0, high=150.0)
alert_engine.register_threshold("aq.orp", low=200.0, high=400.0)
