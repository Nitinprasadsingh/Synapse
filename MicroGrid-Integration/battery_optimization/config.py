"""
config.py
---------
Configuration dataclasses and loader for the MicroGrid Battery Optimization
system.

Hierarchy
~~~~~~~~~
MicrogridConfig
├── TariffConfig       – time-of-use electricity tariffs
├── OptimizationConfig – MPC / MILP solver settings
└── ScalingConfig      – load scaling from county-MW to microgrid-kW

Usage
~~~~~
    from battery_optimization.config import DEFAULT_CONFIG, load_config

    cfg = load_config()                    # reads env vars + optional JSON
    cfg = load_config("my_config.json")    # explicit JSON override

Environment variables (all optional, override defaults)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    MICROGRID_PV_CAPACITY_KW
    MICROGRID_BATTERY_CAPACITY_KWH
    MICROGRID_INITIAL_SOC_PERCENT
    MICROGRID_MIN_SOC_PERCENT
    MICROGRID_MAX_SOC_PERCENT
    MICROGRID_MAX_CHARGE_POWER_KW
    MICROGRID_MAX_DISCHARGE_POWER_KW
    MICROGRID_CHARGE_EFFICIENCY
    MICROGRID_DISCHARGE_EFFICIENCY
    MICROGRID_TIME_STEP_HOURS
    MICROGRID_OPTIMIZATION_HORIZON_HOURS
    MICROGRID_GRID_IMPORT_LIMIT_KW
    MICROGRID_GRID_EXPORT_LIMIT_KW
    MICROGRID_ALLOW_GRID_EXPORT
    MICROGRID_IMPORT_TARIFF_PEAK
    MICROGRID_IMPORT_TARIFF_OFFPEAK
    MICROGRID_EXPORT_TARIFF
    MICROGRID_BATTERY_DEGRADATION_COST_PER_KWH
    MICROGRID_CURTAILMENT_PENALTY_PER_KWH
    MICROGRID_UNSERVED_ENERGY_PENALTY
    MICROGRID_LOAD_SCALING_METHOD
    MICROGRID_LOAD_REFERENCE_MAX_MW
    MICROGRID_LOAD_REFERENCE_MEAN_MW
    MICROGRID_LOAD_SCALE_FACTOR
    MICROGRID_REPRESENTATIVE_PEAK_LOAD_KW
    MICROGRID_MPC_REOPT_INTERVAL_HOURS
    MICROGRID_TERMINAL_SOC_MIN_PERCENT
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Sub-configs
# ---------------------------------------------------------------------------

@dataclass
class TariffConfig:
    """Time-of-use electricity tariffs.

    NOTE: These are SIMULATED tariffs for research/demonstration purposes
    only and do NOT represent real Phoenix APS/SRP utility rate schedules.

    Attributes
    ----------
    import_tariff_peak : float
        Import rate during peak hours ($/kWh).
    import_tariff_offpeak : float
        Import rate during off-peak hours ($/kWh).
    export_tariff : float
        Flat export (feed-in) rate ($/kWh).
    peak_hours : list[int]
        Local America/Phoenix hours (0–23) that are classified as peak.
    battery_degradation_cost_per_kwh : float
        Amortised battery wear cost per kWh of throughput ($/kWh).
    curtailment_penalty_per_kwh : float
        Penalty applied to curtailed PV generation ($/kWh).
    unserved_energy_penalty : float
        Large penalty for load not served ($/kWh) — acts as a soft constraint.
    """

    import_tariff_peak: float = 0.18          # $/kWh (peak 14:00–20:00 local)
    import_tariff_offpeak: float = 0.10       # $/kWh
    export_tariff: float = 0.06               # $/kWh
    peak_hours: List[int] = field(
        default_factory=lambda: [14, 15, 16, 17, 18, 19]
    )
    battery_degradation_cost_per_kwh: float = 0.02   # $/kWh throughput
    curtailment_penalty_per_kwh: float = 0.01         # $/kWh
    unserved_energy_penalty: float = 1000.0           # $/kWh

    def validate(self) -> None:
        """Raise ValueError if any tariff parameter is invalid."""
        if self.import_tariff_peak <= 0:
            raise ValueError(
                f"import_tariff_peak must be > 0, got {self.import_tariff_peak}"
            )
        if self.import_tariff_offpeak <= 0:
            raise ValueError(
                f"import_tariff_offpeak must be > 0, got {self.import_tariff_offpeak}"
            )
        if self.export_tariff < 0:
            raise ValueError(
                f"export_tariff must be >= 0, got {self.export_tariff}"
            )
        if self.import_tariff_offpeak > self.import_tariff_peak:
            raise ValueError(
                "import_tariff_offpeak should not exceed import_tariff_peak "
                "(off-peak should be cheaper than peak)"
            )
        invalid_hours = [h for h in self.peak_hours if not (0 <= h <= 23)]
        if invalid_hours:
            raise ValueError(
                f"All peak_hours must be in [0, 23]; invalid: {invalid_hours}"
            )
        if self.battery_degradation_cost_per_kwh < 0:
            raise ValueError(
                "battery_degradation_cost_per_kwh must be >= 0, got "
                f"{self.battery_degradation_cost_per_kwh}"
            )
        if self.curtailment_penalty_per_kwh < 0:
            raise ValueError(
                "curtailment_penalty_per_kwh must be >= 0, got "
                f"{self.curtailment_penalty_per_kwh}"
            )
        if self.unserved_energy_penalty <= 0:
            raise ValueError(
                "unserved_energy_penalty must be > 0 (it is a soft-constraint "
                f"penalty), got {self.unserved_energy_penalty}"
            )


@dataclass
class OptimizationConfig:
    """MPC / MILP solver settings.

    Attributes
    ----------
    horizon_hours : int
        Rolling optimisation horizon in hours.
    time_step_hours : float
        Duration of each time step (hours). Currently only 1.0 is supported.
    mpc_reopt_interval_hours : int
        How frequently the MPC re-optimises (hours).  Must divide evenly into
        ``horizon_hours``.
    terminal_soc_min_percent : float
        Minimum battery state-of-charge at the end of the horizon (%),
        to avoid draining the battery dry by optimising myopically.
    solver : str
        LP/MIP solver name passed to PuLP (e.g. ``"CBC"``, ``"GLPK"``).
    solver_time_limit_s : Optional[float]
        Wall-clock time limit for the solver per optimisation call (seconds).
        ``None`` means no limit.
    solver_mip_gap : float
        Relative MIP gap tolerance passed to the solver (0.0–1.0).
    """

    horizon_hours: int = 24
    time_step_hours: float = 1.0
    mpc_reopt_interval_hours: int = 1
    terminal_soc_min_percent: float = 50.0
    solver: str = "CBC"
    solver_time_limit_s: Optional[float] = None
    solver_mip_gap: float = 0.001

    def validate(self) -> None:
        """Raise ValueError if any optimisation parameter is invalid."""
        if self.horizon_hours <= 0:
            raise ValueError(
                f"horizon_hours must be > 0, got {self.horizon_hours}"
            )
        if self.time_step_hours <= 0:
            raise ValueError(
                f"time_step_hours must be > 0, got {self.time_step_hours}"
            )
        if self.mpc_reopt_interval_hours <= 0:
            raise ValueError(
                "mpc_reopt_interval_hours must be > 0, got "
                f"{self.mpc_reopt_interval_hours}"
            )
        if self.horizon_hours % self.mpc_reopt_interval_hours != 0:
            raise ValueError(
                f"mpc_reopt_interval_hours ({self.mpc_reopt_interval_hours}) "
                f"must divide evenly into horizon_hours ({self.horizon_hours})"
            )
        if not (0.0 <= self.terminal_soc_min_percent <= 100.0):
            raise ValueError(
                "terminal_soc_min_percent must be in [0, 100], got "
                f"{self.terminal_soc_min_percent}"
            )
        if self.solver_time_limit_s is not None and self.solver_time_limit_s <= 0:
            raise ValueError(
                "solver_time_limit_s must be > 0 or None, got "
                f"{self.solver_time_limit_s}"
            )
        if not (0.0 <= self.solver_mip_gap < 1.0):
            raise ValueError(
                f"solver_mip_gap must be in [0, 1), got {self.solver_mip_gap}"
            )


@dataclass
class ScalingConfig:
    """Load scaling configuration — maps county-level MW forecasts to
    microgrid-level kW.

    Three methods are supported:

    ``"peak"`` (default)
        Normalises by the historical county maximum:
        ``Load_microgrid = (Load_county / reference_max_mw) × representative_peak_load_kw``

    ``"average"``
        Normalises by the historical county mean:
        ``Load_microgrid = (Load_county / reference_mean_mw) × representative_peak_load_kw``

    ``"factor"``
        Applies a fixed multiplicative factor (MW → kW):
        ``Load_microgrid = Load_county × scale_factor × 1000``
        where *scale_factor* is the fraction of the county load attributed to
        the microgrid.  Must set ``scale_factor`` explicitly.

    Attributes
    ----------
    method : str
        One of ``"peak"``, ``"average"``, ``"factor"``.
    reference_max_mw : float
        Historical maximum county load in MW (from load_clean_2017_2019.csv).
    reference_mean_mw : float
        Historical mean county load in MW.
    scale_factor : Optional[float]
        Dimensionless fraction for the ``"factor"`` method.
    representative_peak_load_kw : float
        Target peak load for the microgrid in kW.
    """

    method: str = "peak"
    reference_max_mw: float = 11554.97      # from load_clean_2017_2019.csv
    reference_mean_mw: float = 5512.76      # from load_clean_2017_2019.csv
    scale_factor: Optional[float] = None
    representative_peak_load_kw: float = 80.0

    def validate(self) -> None:
        """Raise ValueError if any scaling parameter is invalid."""
        valid_methods = {"peak", "average", "factor"}
        if self.method not in valid_methods:
            raise ValueError(
                f"method must be one of {valid_methods}, got {self.method!r}"
            )
        if self.method == "factor" and self.scale_factor is None:
            raise ValueError(
                "scale_factor must be set when method='factor'"
            )
        if self.scale_factor is not None and self.scale_factor <= 0:
            raise ValueError(
                f"scale_factor must be > 0, got {self.scale_factor}"
            )
        if self.reference_max_mw <= 0:
            raise ValueError(
                f"reference_max_mw must be > 0, got {self.reference_max_mw}"
            )
        if self.reference_mean_mw <= 0:
            raise ValueError(
                f"reference_mean_mw must be > 0, got {self.reference_mean_mw}"
            )
        if self.representative_peak_load_kw <= 0:
            raise ValueError(
                "representative_peak_load_kw must be > 0, got "
                f"{self.representative_peak_load_kw}"
            )

    def scale_mw_to_kw(self, load_mw: float) -> float:
        """Convert a single county load value (MW) to microgrid kW.

        Parameters
        ----------
        load_mw : float
            County-level load in MW.

        Returns
        -------
        float
            Microgrid-level load in kW.
        """
        if self.method == "peak":
            return (load_mw / self.reference_max_mw) * self.representative_peak_load_kw
        elif self.method == "average":
            return (load_mw / self.reference_mean_mw) * self.representative_peak_load_kw
        elif self.method == "factor":
            # scale_factor is a dimensionless fraction; ×1000 to convert MW→kW
            return load_mw * self.scale_factor * 1000.0  # type: ignore[operator]
        else:  # should never reach here after validate()
            raise ValueError(f"Unknown scaling method: {self.method!r}")


# ---------------------------------------------------------------------------
# Top-level config
# ---------------------------------------------------------------------------

@dataclass
class MicrogridConfig:
    """Top-level configuration for the MicroGrid Battery Optimisation system.

    Attributes
    ----------
    pv_capacity_kw : float
        Rated DC capacity of the PV system (kW).
    battery_capacity_kwh : float
        Usable energy capacity of the battery (kWh).
    initial_soc_percent : float
        Battery state-of-charge at the start of optimisation (%).
    min_soc_percent : float
        Hard lower bound on battery SoC (%).
    max_soc_percent : float
        Hard upper bound on battery SoC (%).
    max_charge_power_kw : float
        Maximum battery charging power (kW).
    max_discharge_power_kw : float
        Maximum battery discharging power (kW).
    charge_efficiency : float
        One-way charging efficiency (fraction, 0 < η ≤ 1).
    discharge_efficiency : float
        One-way discharging efficiency (fraction, 0 < η ≤ 1).
    grid_import_limit_kw : float
        Maximum power that can be drawn from the grid (kW).
    grid_export_limit_kw : float
        Maximum power that can be exported to the grid (kW).
    allow_grid_export : bool
        Whether grid export is permitted at all.
    tariff : TariffConfig
        Time-of-use tariff settings.
    optimization : OptimizationConfig
        MPC / solver settings.
    scaling : ScalingConfig
        Load scaling settings.
    timezone : str
        IANA timezone string used for all operational timestamps.
    """

    # Physical parameters
    pv_capacity_kw: float = 100.0
    battery_capacity_kwh: float = 200.0
    initial_soc_percent: float = 50.0
    min_soc_percent: float = 10.0
    max_soc_percent: float = 90.0
    max_charge_power_kw: float = 50.0
    max_discharge_power_kw: float = 50.0
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.95
    grid_import_limit_kw: float = 100.0
    grid_export_limit_kw: float = 100.0
    allow_grid_export: bool = True

    # Nested sub-configs
    tariff: TariffConfig = field(default_factory=TariffConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    scaling: ScalingConfig = field(default_factory=ScalingConfig)

    # Timezone
    timezone: str = "America/Phoenix"

    @property
    def battery(self) -> "MicrogridConfig":
        """Compatibility view used by baseline and visualization modules."""
        return self

    @property
    def capacity_kwh(self) -> float:
        return self.battery_capacity_kwh

    @property
    def max_charge_kw(self) -> float:
        return self.max_charge_power_kw

    @property
    def max_discharge_kw(self) -> float:
        return self.max_discharge_power_kw

    @property
    def soc_min_percent(self) -> float:
        return self.min_soc_percent

    @property
    def soc_min_kwh(self) -> float:
        return self.battery_capacity_kwh * self.min_soc_percent / 100.0

    @property
    def max_soc_kwh(self) -> float:
        return self.battery_capacity_kwh * self.max_soc_percent / 100.0

    @property
    def round_trip_efficiency(self) -> float:
        return self.charge_efficiency * self.discharge_efficiency

    @property
    def degradation_cost_per_kwh(self) -> float:
        return self.tariff.battery_degradation_cost_per_kwh

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """Validate all parameters; raise ValueError on the first violation.

        Rules
        -----
        - ``min_soc_percent < max_soc_percent``
        - ``max_soc_percent <= 100``
        - ``min_soc_percent >= 0``
        - ``initial_soc_percent`` ∈ [``min_soc_percent``, ``max_soc_percent``]
        - ``battery_capacity_kwh > 0``
        - ``max_charge_power_kw > 0``
        - ``max_discharge_power_kw > 0``
        - ``charge_efficiency`` ∈ (0, 1]
        - ``discharge_efficiency`` ∈ (0, 1]
        - ``pv_capacity_kw > 0``
        - ``grid_import_limit_kw >= 0``
        - ``grid_export_limit_kw >= 0``
        - All nested sub-configs are individually validated.
        """
        # SoC bounds
        if self.min_soc_percent < 0:
            raise ValueError(
                f"min_soc_percent must be >= 0, got {self.min_soc_percent}"
            )
        if self.max_soc_percent > 100:
            raise ValueError(
                f"max_soc_percent must be <= 100, got {self.max_soc_percent}"
            )
        if self.min_soc_percent >= self.max_soc_percent:
            raise ValueError(
                f"min_soc_percent ({self.min_soc_percent}) must be strictly "
                f"less than max_soc_percent ({self.max_soc_percent})"
            )
        if not (self.min_soc_percent <= self.initial_soc_percent <= self.max_soc_percent):
            raise ValueError(
                f"initial_soc_percent ({self.initial_soc_percent}) must be "
                f"within [min_soc_percent, max_soc_percent] = "
                f"[{self.min_soc_percent}, {self.max_soc_percent}]"
            )

        # Battery
        if self.battery_capacity_kwh <= 0:
            raise ValueError(
                f"battery_capacity_kwh must be > 0, got {self.battery_capacity_kwh}"
            )
        if self.max_charge_power_kw <= 0:
            raise ValueError(
                f"max_charge_power_kw must be > 0, got {self.max_charge_power_kw}"
            )
        if self.max_discharge_power_kw <= 0:
            raise ValueError(
                f"max_discharge_power_kw must be > 0, got {self.max_discharge_power_kw}"
            )

        # Efficiencies
        if not (0 < self.charge_efficiency <= 1.0):
            raise ValueError(
                f"charge_efficiency must be in (0, 1], got {self.charge_efficiency}"
            )
        if not (0 < self.discharge_efficiency <= 1.0):
            raise ValueError(
                "discharge_efficiency must be in (0, 1], got "
                f"{self.discharge_efficiency}"
            )

        # PV
        if self.pv_capacity_kw <= 0:
            raise ValueError(
                f"pv_capacity_kw must be > 0, got {self.pv_capacity_kw}"
            )

        # Grid
        if self.grid_import_limit_kw < 0:
            raise ValueError(
                f"grid_import_limit_kw must be >= 0, got {self.grid_import_limit_kw}"
            )
        if self.grid_export_limit_kw < 0:
            raise ValueError(
                f"grid_export_limit_kw must be >= 0, got {self.grid_export_limit_kw}"
            )

        # Nested configs
        self.tariff.validate()
        self.optimization.validate()
        self.scaling.validate()

        # Cross-config consistency
        if self.optimization.terminal_soc_min_percent > self.max_soc_percent:
            raise ValueError(
                f"terminal_soc_min_percent ({self.optimization.terminal_soc_min_percent}) "
                f"exceeds max_soc_percent ({self.max_soc_percent})"
            )
        if self.optimization.terminal_soc_min_percent < self.min_soc_percent:
            raise ValueError(
                f"terminal_soc_min_percent ({self.optimization.terminal_soc_min_percent}) "
                f"is below min_soc_percent ({self.min_soc_percent})"
            )

    def to_dict(self) -> dict:
        """Serialise the entire config to a plain dict (JSON-serialisable)."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Default instance
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = MicrogridConfig()
DEFAULT_CONFIG.validate()  # sanity-check defaults at import time


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def _env_float(key: str, default: Optional[float]) -> Optional[float]:
    val = os.environ.get(key)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError as exc:
        raise ValueError(
            f"Environment variable {key}={val!r} cannot be parsed as float"
        ) from exc


def _env_int(key: str, default: int) -> int:
    val = os.environ.get(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError as exc:
        raise ValueError(
            f"Environment variable {key}={val!r} cannot be parsed as int"
        ) from exc


def _env_bool(key: str, default: bool) -> bool:
    val = os.environ.get(key)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes"}


def load_config(json_path: Optional[str] = None) -> MicrogridConfig:
    """Build a :class:`MicrogridConfig` from defaults, an optional JSON file,
    and environment variables.

    Resolution order (later overrides earlier):
    1. Hard-coded defaults (``MicrogridConfig`` field defaults)
    2. JSON file (if *json_path* is provided or ``MICROGRID_CONFIG_PATH`` env
       var is set)
    3. Individual environment variables (``MICROGRID_*``)

    Parameters
    ----------
    json_path : str, optional
        Path to a JSON config file.  Top-level keys map to
        :class:`MicrogridConfig` field names; nested dicts map to
        :class:`TariffConfig`, :class:`OptimizationConfig`, and
        :class:`ScalingConfig`.  Unknown keys are silently ignored.

    Returns
    -------
    MicrogridConfig
        A validated configuration instance.

    Raises
    ------
    ValueError
        If any parameter fails validation.
    FileNotFoundError
        If *json_path* is given but the file does not exist.
    json.JSONDecodeError
        If the JSON file is malformed.

    Example
    -------
    ::

        import os
        os.environ["MICROGRID_BATTERY_CAPACITY_KWH"] = "400.0"
        from battery_optimization.config import load_config
        cfg = load_config("my_site.json")
    """
    # 1. Start from defaults
    tariff_kw: dict = dict(
        import_tariff_peak=0.18,
        import_tariff_offpeak=0.10,
        export_tariff=0.06,
        peak_hours=[14, 15, 16, 17, 18, 19],
        battery_degradation_cost_per_kwh=0.02,
        curtailment_penalty_per_kwh=0.01,
        unserved_energy_penalty=1000.0,
    )
    opt_kw: dict = dict(
        horizon_hours=24,
        time_step_hours=1.0,
        mpc_reopt_interval_hours=1,
        terminal_soc_min_percent=50.0,
        solver="CBC",
        solver_time_limit_s=None,
        solver_mip_gap=0.001,
    )
    scaling_kw: dict = dict(
        method="peak",
        reference_max_mw=11554.97,
        reference_mean_mw=5512.76,
        scale_factor=None,
        representative_peak_load_kw=80.0,
    )
    top_kw: dict = dict(
        pv_capacity_kw=100.0,
        battery_capacity_kwh=200.0,
        initial_soc_percent=50.0,
        min_soc_percent=10.0,
        max_soc_percent=90.0,
        max_charge_power_kw=50.0,
        max_discharge_power_kw=50.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        grid_import_limit_kw=100.0,
        grid_export_limit_kw=100.0,
        allow_grid_export=True,
        timezone="America/Phoenix",
    )

    # 2. JSON file
    resolved_path = json_path or os.environ.get("MICROGRID_CONFIG_PATH")
    if resolved_path:
        p = Path(resolved_path)
        if not p.exists():
            raise FileNotFoundError(
                f"Config file not found: {p.resolve()}"
            )
        with open(p, "r", encoding="utf-8") as fh:
            file_data: dict = json.load(fh)

        for k, v in file_data.items():
            if k == "tariff" and isinstance(v, dict):
                tariff_kw.update(v)
            elif k == "optimization" and isinstance(v, dict):
                opt_kw.update(v)
            elif k == "scaling" and isinstance(v, dict):
                scaling_kw.update(v)
            elif k in top_kw:
                top_kw[k] = v

    # 3. Environment variable overrides
    top_kw["pv_capacity_kw"] = _env_float(
        "MICROGRID_PV_CAPACITY_KW", top_kw["pv_capacity_kw"]
    )
    top_kw["battery_capacity_kwh"] = _env_float(
        "MICROGRID_BATTERY_CAPACITY_KWH", top_kw["battery_capacity_kwh"]
    )
    top_kw["initial_soc_percent"] = _env_float(
        "MICROGRID_INITIAL_SOC_PERCENT", top_kw["initial_soc_percent"]
    )
    top_kw["min_soc_percent"] = _env_float(
        "MICROGRID_MIN_SOC_PERCENT", top_kw["min_soc_percent"]
    )
    top_kw["max_soc_percent"] = _env_float(
        "MICROGRID_MAX_SOC_PERCENT", top_kw["max_soc_percent"]
    )
    top_kw["max_charge_power_kw"] = _env_float(
        "MICROGRID_MAX_CHARGE_POWER_KW", top_kw["max_charge_power_kw"]
    )
    top_kw["max_discharge_power_kw"] = _env_float(
        "MICROGRID_MAX_DISCHARGE_POWER_KW", top_kw["max_discharge_power_kw"]
    )
    top_kw["charge_efficiency"] = _env_float(
        "MICROGRID_CHARGE_EFFICIENCY", top_kw["charge_efficiency"]
    )
    top_kw["discharge_efficiency"] = _env_float(
        "MICROGRID_DISCHARGE_EFFICIENCY", top_kw["discharge_efficiency"]
    )
    top_kw["grid_import_limit_kw"] = _env_float(
        "MICROGRID_GRID_IMPORT_LIMIT_KW", top_kw["grid_import_limit_kw"]
    )
    top_kw["grid_export_limit_kw"] = _env_float(
        "MICROGRID_GRID_EXPORT_LIMIT_KW", top_kw["grid_export_limit_kw"]
    )
    top_kw["allow_grid_export"] = _env_bool(
        "MICROGRID_ALLOW_GRID_EXPORT", top_kw["allow_grid_export"]
    )

    tariff_kw["import_tariff_peak"] = _env_float(
        "MICROGRID_IMPORT_TARIFF_PEAK", tariff_kw["import_tariff_peak"]
    )
    tariff_kw["import_tariff_offpeak"] = _env_float(
        "MICROGRID_IMPORT_TARIFF_OFFPEAK", tariff_kw["import_tariff_offpeak"]
    )
    tariff_kw["export_tariff"] = _env_float(
        "MICROGRID_EXPORT_TARIFF", tariff_kw["export_tariff"]
    )
    tariff_kw["battery_degradation_cost_per_kwh"] = _env_float(
        "MICROGRID_BATTERY_DEGRADATION_COST_PER_KWH",
        tariff_kw["battery_degradation_cost_per_kwh"],
    )
    tariff_kw["curtailment_penalty_per_kwh"] = _env_float(
        "MICROGRID_CURTAILMENT_PENALTY_PER_KWH",
        tariff_kw["curtailment_penalty_per_kwh"],
    )
    tariff_kw["unserved_energy_penalty"] = _env_float(
        "MICROGRID_UNSERVED_ENERGY_PENALTY", tariff_kw["unserved_energy_penalty"]
    )

    scaling_kw["method"] = os.environ.get(
        "MICROGRID_LOAD_SCALING_METHOD", scaling_kw["method"]
    )
    scaling_kw["reference_max_mw"] = _env_float(
        "MICROGRID_LOAD_REFERENCE_MAX_MW", scaling_kw["reference_max_mw"]
    )
    scaling_kw["reference_mean_mw"] = _env_float(
        "MICROGRID_LOAD_REFERENCE_MEAN_MW", scaling_kw["reference_mean_mw"]
    )
    scaling_kw["scale_factor"] = _env_float(
        "MICROGRID_LOAD_SCALE_FACTOR", scaling_kw["scale_factor"]
    )
    scaling_kw["representative_peak_load_kw"] = _env_float(
        "MICROGRID_REPRESENTATIVE_PEAK_LOAD_KW",
        scaling_kw["representative_peak_load_kw"],
    )

    opt_kw["mpc_reopt_interval_hours"] = _env_int(
        "MICROGRID_MPC_REOPT_INTERVAL_HOURS", opt_kw["mpc_reopt_interval_hours"]
    )
    opt_kw["terminal_soc_min_percent"] = _env_float(
        "MICROGRID_TERMINAL_SOC_MIN_PERCENT", opt_kw["terminal_soc_min_percent"]
    )

    # Build nested dataclasses
    tariff = TariffConfig(**tariff_kw)
    optimization = OptimizationConfig(**opt_kw)
    scaling = ScalingConfig(**scaling_kw)

    cfg = MicrogridConfig(
        **top_kw,
        tariff=tariff,
        optimization=optimization,
        scaling=scaling,
    )
    cfg.validate()
    return cfg
