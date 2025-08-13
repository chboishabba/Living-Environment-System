import pytest

from les.state import StateRegistry


def test_state_registry_register_and_get():
    registry = StateRegistry()
    registry.register('foo', 1)
    assert registry.get('foo') == 1


def test_state_registry_set_updates_and_error_on_unregistered():
    registry = StateRegistry()
    registry.register('foo', 1)
    registry.set('foo', 2)
    assert registry.get('foo') == 2
    with pytest.raises(KeyError):
        registry.set('bar', 3)
    with pytest.raises(KeyError):
        registry.get('bar')
