"""Event logging utilities for the Living Environment System."""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union

from .types import EventType

# In-memory list of event dictionaries
_EVENT_LOG: List[Dict[str, str]] = []

# CSV file to persist events between runs
_EVENT_LOG_FILE = Path(__file__).with_name("events.csv")

def log_event(event_type: Union[str, EventType], details: str) -> None:
    """Log an event with a type and details.

    The event is stored in-memory and appended to a CSV file for persistence.
    ``event_type`` may be either a string or an :class:`EventType` enum member.
    """
    event_type_str = event_type.value if isinstance(event_type, EventType) else event_type
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type_str,
        "details": details,
    }
    _EVENT_LOG.append(entry)
    _EVENT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_exists = _EVENT_LOG_FILE.exists()
    with _EVENT_LOG_FILE.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "event_type", "details"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(entry)

def get_recent_events(limit: int = 5) -> List[Dict[str, str]]:
    """Return the most recent events up to ``limit`` entries."""
    if not _EVENT_LOG and _EVENT_LOG_FILE.exists():
        with _EVENT_LOG_FILE.open("r", newline="") as f:
            reader = csv.DictReader(f)
            _EVENT_LOG.extend(reader)
    return _EVENT_LOG[-limit:]
