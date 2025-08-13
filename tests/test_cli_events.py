import sys
import pytest

from les.cli import show_recent_events, main
from les.modules.events import logger
from les.modules.events.types import EventType


def test_show_recent_events_output(capsys, tmp_path, monkeypatch):
    """Ensure show_recent_events prints logged events."""
    # Start with a clean in-memory log and temporary file
    monkeypatch.setattr(logger, "_EVENT_LOG", [])
    monkeypatch.setattr(logger, "_EVENT_LOG_FILE", tmp_path / "events.csv")

    # Log sample events
    logger.log_event(EventType.FILTER_CHANGE, "Filter replaced")
    logger.log_event(EventType.HARDWARE_FAILURE, "Pump failure")

    # Display recent events and capture output
    show_recent_events()
    captured = capsys.readouterr()

    # Verify both events appear in output
    assert "filter_change: Filter replaced" in captured.out
    assert "hardware_failure: Pump failure" in captured.out


def test_cli_main_logs_and_shows_events(capsys, tmp_path, monkeypatch):
    """CLI should log a new event and then display it."""
    monkeypatch.setattr(logger, "_EVENT_LOG", [])
    monkeypatch.setattr(logger, "_EVENT_LOG_FILE", tmp_path / "events.csv")

    # Simulate CLI arguments for logging and showing events
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prog",
            "--log-event",
            "filter_change",
            "Filter replaced",
            "--show-events",
        ],
    )

    main()
    captured = capsys.readouterr()
    assert "filter_change: Filter replaced" in captured.out
