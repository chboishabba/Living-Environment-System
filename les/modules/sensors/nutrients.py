"""Sensor polling utilities for nutrient probes."""
from __future__ import annotations
import time
from typing import Optional


def _poll_probe(address: int, i2c_bus: int = 1) -> Optional[float]:
    """Read a value from an Atlas Scientific I²C probe.

    Parameters
    ----------
    address: int
        I²C address of the probe to poll.
    i2c_bus: int, optional
        The I²C bus number to use, defaulting to ``1``.

    Returns
    -------
    Optional[float]
        Parsed floating point value from the probe, or ``None`` if unavailable
        or invalid.
    """
    try:
        import smbus2
    except ImportError:  # pragma: no cover - hardware dependency
        return None

    bus = smbus2.SMBus(i2c_bus)
    bus.write_byte(address, ord("R"))
    time.sleep(1.0)
    data = bus.read_i2c_block_data(address, 0, 32)
    text = bytes([d for d in data if d != 0]).decode().strip()
    try:
        return float(text)
    except ValueError:
        return None


def poll_nitrate(i2c_bus: int = 1) -> Optional[float]:
    """Poll an Atlas Scientific EZO-NO3 nitrate probe.

    Parameters
    ----------
    i2c_bus: int
        I2C bus number to use.

    Returns
    -------
    Optional[float]
        Nitrate concentration in mg/L if read succeeds, otherwise ``None``.
    """
    return _poll_probe(0x64, i2c_bus=i2c_bus)


def poll_orp(i2c_bus: int = 1) -> Optional[float]:
    """Poll an Atlas Scientific EZO-ORP probe.

    Returns the oxidation-reduction potential in millivolts.
    """
    return _poll_probe(0x62, i2c_bus=i2c_bus)
