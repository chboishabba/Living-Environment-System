import sys
import types
import builtins

import pytest

from les.modules.sensors.nutrients import poll_nitrate, poll_orp


def _fake_bus_factory(data):
    class FakeBus:
        def __init__(self, bus):
            pass

        def write_byte(self, address, value):
            pass

        def read_i2c_block_data(self, address, register, length):
            return data
    return FakeBus


@pytest.mark.parametrize(
    "func,value",
    [
        (poll_nitrate, "123.45"),
        (poll_orp, "67.89"),
    ],
)
def test_poll_parses_float(monkeypatch, func, value):
    data = [ord(c) for c in value] + [0, 0]
    fake_module = types.SimpleNamespace(SMBus=_fake_bus_factory(data))
    monkeypatch.setitem(sys.modules, "smbus2", fake_module)
    monkeypatch.setattr("time.sleep", lambda x: None)
    assert func() == pytest.approx(float(value))


@pytest.mark.parametrize("func", [poll_nitrate, poll_orp])
def test_poll_returns_none_on_invalid_data(monkeypatch, func):
    data = [ord(c) for c in "invalid"]
    fake_module = types.SimpleNamespace(SMBus=_fake_bus_factory(data))
    monkeypatch.setitem(sys.modules, "smbus2", fake_module)
    monkeypatch.setattr("time.sleep", lambda x: None)
    assert func() is None


@pytest.mark.parametrize("func", [poll_nitrate, poll_orp])
def test_poll_returns_none_on_import_error(monkeypatch, func):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "smbus2":
            raise ImportError
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.delitem(sys.modules, "smbus2", raising=False)
    monkeypatch.setattr("time.sleep", lambda x: None)
    assert func() is None
