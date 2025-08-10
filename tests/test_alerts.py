from les.state import state
from les.alerts import alert_engine


def test_threshold_alerts_trigger():
    state.set('aq.nitrate', 200)
    state.set('aq.orp', 100)
    alerts = alert_engine.check(state)
    assert any('aq.nitrate' in a for a in alerts)
    assert any('aq.orp' in a for a in alerts)


def test_threshold_alerts_clear():
    state.set('aq.nitrate', 50)
    state.set('aq.orp', 300)
    alerts = alert_engine.check(state)
    assert alerts == []
