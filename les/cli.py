"""Simple CLI for interacting with the Living Environment System."""
import argparse

from .modules.events.logger import get_recent_events, log_event
from .modules.events.types import EventType

def show_recent_events(limit: int = 5) -> None:
    """Print recent events to stdout."""
    events = get_recent_events(limit)
    for event in events:
        print(f"{event['timestamp']} - {event['event_type']}: {event['details']}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Living Environment System CLI")
    parser.add_argument("--show-events", action="store_true", help="Display recent events")
    parser.add_argument("--limit", type=int, default=5, help="Number of events to display")
    parser.add_argument("--log-event", nargs=2, metavar=("TYPE", "DETAILS"), help="Log a new event")
    args = parser.parse_args()

    if args.log_event:
        event_type, details = args.log_event
        log_event(event_type, details)

    if args.show_events:
        show_recent_events(args.limit)

if __name__ == "__main__":
    main()
