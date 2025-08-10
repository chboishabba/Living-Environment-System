"""Sensor polling utilities for nutrient probes."""
from __future__ import annotations
import time
from typing import Optional


def poll_nitrate(i2c_bus: int = 1, address: int = 0x64) -> Optional[float]:
    """Poll an Atlas Scientific EZO-NO3 nitrate probe.

    Parameters
    ----------
    i2c_bus: int
        I2C bus number to use.
    address: int
        I2C address of the probe.

    Returns
    -------
    Optional[float]
        Nitrate concentration in mg/L if read succeeds, otherwise ``None``.
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


def poll_orp(i2c_bus: int = 1, address: int = 0x62) -> Optional[float]:
    """Poll an Atlas Scientific EZO-ORP probe.

    Returns the oxidation-reduction potential in millivolts.
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
