"""
tariff_utils.py
---------------
Utility functions for time-of-use (TOU) tariff lookups.

NOTE: The tariff rates in this project are SIMULATED and do NOT represent
real Phoenix APS/SRP utility tariff schedules. They are designed for
research and demonstration purposes only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from battery_optimization.config import TariffConfig


def get_import_tariff(hour: int, config: "TariffConfig") -> float:
    """Return the import electricity tariff ($/kWh) for a given local Phoenix hour.

    Parameters
    ----------
    hour : int
        The local hour of day in America/Phoenix time (0–23).
    config : TariffConfig
        A TariffConfig instance with peak_hours, import_tariff_peak, and
        import_tariff_offpeak attributes.

    Returns
    -------
    float
        The applicable import tariff in $/kWh.

    Raises
    ------
    ValueError
        If *hour* is outside [0, 23].

    Notes
    -----
    Peak hours are defined in ``config.peak_hours`` (default 14–19 local
    Phoenix time, i.e. 2 PM – 7 PM).  All other hours are off-peak.

    Example
    -------
    >>> from battery_optimization.config import DEFAULT_CONFIG
    >>> get_import_tariff(15, DEFAULT_CONFIG.tariff)
    0.18
    >>> get_import_tariff(10, DEFAULT_CONFIG.tariff)
    0.1
    """
    if not (0 <= hour <= 23):
        raise ValueError(f"hour must be in [0, 23], got {hour!r}")

    if hour in config.peak_hours:
        return config.import_tariff_peak
    return config.import_tariff_offpeak


def get_export_tariff(hour: int, config: "TariffConfig") -> float:  # noqa: ARG001
    """Return the export electricity tariff ($/kWh) for a given local Phoenix hour.

    Currently a flat rate regardless of hour, but the signature accepts *hour*
    so callers do not need to change when time-varying export rates are added.

    Parameters
    ----------
    hour : int
        The local hour of day in America/Phoenix time (0–23).
    config : TariffConfig
        A TariffConfig instance with the ``export_tariff`` attribute.

    Returns
    -------
    float
        The applicable export tariff in $/kWh.
    """
    if not (0 <= hour <= 23):
        raise ValueError(f"hour must be in [0, 23], got {hour!r}")

    return config.export_tariff
