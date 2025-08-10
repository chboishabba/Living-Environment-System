from enum import Enum

class EventType(str, Enum):
    """Common event types for the Living Environment System."""
    FILTER_CHANGE = "filter_change"
    MORTALITIES = "mortalities"
    HARDWARE_FAILURE = "hardware_failure"
