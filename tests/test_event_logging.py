import csv

from les.modules.events import logger


def test_log_event_persists_and_limits(tmp_path, monkeypatch):
    temp_file = tmp_path / "events.csv"
    monkeypatch.setattr(logger, "_EVENT_LOG_FILE", temp_file)
    logger._EVENT_LOG.clear()

    logger.log_event("type1", "first event")
    logger.log_event("type2", "second event")

    events = logger.get_recent_events(limit=1)
    assert len(events) == 1
    assert events[0]["event_type"] == "type2"

    assert len(logger._EVENT_LOG) == 2

    with temp_file.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
