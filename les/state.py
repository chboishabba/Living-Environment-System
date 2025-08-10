"""State registry for LES."""
from typing import Any, Dict


class StateRegistry:
    """Simple dictionary-backed state registry."""

    def __init__(self) -> None:
        self._state: Dict[str, Any] = {}

    def register(self, key: str, value: Any = None) -> None:
        """Register a new state variable."""
        self._state[key] = value

    def set(self, key: str, value: Any) -> None:
        if key not in self._state:
            raise KeyError(f"Variable {key!r} is not registered")
        self._state[key] = value

    def get(self, key: str) -> Any:
        if key not in self._state:
            raise KeyError(f"Variable {key!r} is not registered")
        return self._state[key]


# Global registry instance
state = StateRegistry()
state.register("aq.nitrate")
state.register("aq.orp")
