"""
scheduler.py
------------
Rolling-horizon Model Predictive Control (MPC) scheduler for the
MicroGrid Battery Optimization system.

The MPCScheduler orchestrates the MPC loop:
  - At each hourly timestep it fetches a 24-hour forecast window,
    runs the BatteryOptimizer over that window, applies only the
    first decision, updates the battery state-of-charge, records the
    result, then advances one hour.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

import pandas as pd
from zoneinfo import ZoneInfo

from battery_optimization.exceptions import ForecastError, OptimizationError
from battery_optimization.tariff_utils import get_export_tariff, get_import_tariff

if TYPE_CHECKING:
    from battery_optimization.config import MicrogridConfig
    from battery_optimization.forecast_integration import ForecastIntegrationService
    from battery_optimization.optimizer import BatteryOptimizer

logger = logging.getLogger(__name__)

PHOENIX_TZ = ZoneInfo("America/Phoenix")


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class SimulationResult:
    """Container for a completed MPC simulation run.

    Attributes
    ----------
    schedule : pd.DataFrame
        One row per executed timestep with all decision variables and costs.
    metrics : dict
        Aggregate KPIs for the full simulation window.
    solver_statuses : list of str
        CVXPY / solver status string from every optimisation call.
    """

    schedule: pd.DataFrame
    metrics: dict
    solver_statuses: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# MPC Scheduler
# ---------------------------------------------------------------------------


class MPCScheduler:
    """Rolling-horizon Model Predictive Control scheduler.

    Parameters
    ----------
    optimizer : BatteryOptimizer
        Pre-configured optimiser instance (from battery_optimization.optimizer).
    forecast_service : ForecastIntegrationService
        Service that returns PV and load forecasts for a given time window.
    config : MicrogridConfig
        System-wide configuration (battery, tariff, PV system, etc.).
    """

    def __init__(
        self,
        optimizer: "BatteryOptimizer",
        forecast_service: "ForecastIntegrationService",
        config: "MicrogridConfig",
    ) -> None:
        self.optimizer = optimizer
        self.forecast_service = forecast_service
        self.config = config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_simulation(
        self,
        start_time: pd.Timestamp,
        simulation_hours: int = 24,
        initial_soc_percent: Optional[float] = None,
    ) -> SimulationResult:
        """Run an MPC simulation for *simulation_hours* starting at *start_time*.

        MPC workflow per timestep
        -------------------------
        1. Get the latest 24-hour PV + load forecast starting from *current_time*.
        2. Run the optimiser with the current SOC as the initial condition.
        3. Extract **only** the first timestep action
           (charge / discharge / grid-import / grid-export).
        4. Update SOC:
           ``soc_new = soc_old + η·charge·Δt − discharge·Δt/η``
        5. Record the timestep results.
        6. Advance time by one hour.
        7. Repeat until *simulation_hours* steps are complete.

        Parameters
        ----------
        start_time : pd.Timestamp
            UTC (or timezone-aware) start of the simulation.
        simulation_hours : int, optional
            Number of hourly steps to simulate (default 24).
        initial_soc_percent : float, optional
            Initial battery SOC as a percentage of usable capacity.
            Defaults to ``config.battery.initial_soc_percent``.

        Returns
        -------
        SimulationResult
            Dataclass containing the full schedule DataFrame and aggregate metrics.
        """
        battery_cfg = self.config
        tariff_cfg = self.config.tariff

        # ---- Initialise SOC ------------------------------------------------
        if initial_soc_percent is None:
            initial_soc_percent = getattr(battery_cfg, "initial_soc_percent", 50.0)

        if simulation_hours <= 0:
            raise ValueError("simulation_hours must be positive")
        soc_kwh: float = (initial_soc_percent / 100.0) * battery_cfg.battery_capacity_kwh

        # ---- Storage for per-step records ----------------------------------
        rows: list[dict] = []
        solver_statuses: list[str] = []
        horizon_hours: int = self.config.optimization.horizon_hours

        current_time = pd.Timestamp(start_time)
        if current_time.tzinfo is None:
            current_time = current_time.tz_localize("UTC")

        for step in range(simulation_hours):
            logger.debug("MPC step %d/%d  t=%s  soc=%.2f kWh",
                         step + 1, simulation_hours, current_time, soc_kwh)

            # 1. Fetch forecast --------------------------------------------------
            try:
                forecast = self.forecast_service.get_forecast(
                    start_time=current_time,
                    horizon_hours=horizon_hours,
                )
                pv_forecast_kw: list[float] = forecast["pv_kw"]
                load_forecast_kw: list[float] = forecast["load_kw"]
            except ForecastError:
                raise

            # 2. Build tariff vectors for the horizon ----------------------------
            import_tariffs = self._get_import_tariffs(current_time, horizon_hours)
            export_tariffs = [
                get_export_tariff(
                    self._local_hour(current_time + pd.Timedelta(hours=h)), tariff_cfg
                )
                for h in range(horizon_hours)
            ]

            # 3. Run optimiser over the full horizon ----------------------------
            try:
                opt_result = self.optimizer.optimize(
                    pv_forecast_kw=pv_forecast_kw,
                    load_forecast_kw=load_forecast_kw,
                    import_tariffs=import_tariffs,
                    export_tariffs=export_tariffs,
                    initial_soc_kwh=soc_kwh,
                )
                solver_status = opt_result.get("status", "unknown")
                # Extract first-step decisions
                charge_kw = float(opt_result["battery_charge_kw"][0])
                discharge_kw = float(opt_result["battery_discharge_kw"][0])
                grid_import_kw = float(opt_result["grid_import_kw"][0])
                grid_export_kw = float(opt_result["grid_export_kw"][0])
                curtailment_kw = float(opt_result.get("solar_curtailment_kw", [0.0])[0])
                battery_degradation_cost = float(
                    opt_result.get("battery_degradation_cost", [0.0])[0]
                )
            except OptimizationError:
                raise

            solver_statuses.append(solver_status)

            # 4. Update SOC ------------------------------------------------------
            soc_kwh = self._update_soc(soc_kwh, charge_kw, discharge_kw)

            # 5. Record results --------------------------------------------------
            pv0 = pv_forecast_kw[0]
            load0 = load_forecast_kw[0]
            local_hour = self._local_hour(current_time)
            import_tariff_val = import_tariffs[0]
            export_tariff_step = export_tariffs[0]

            grid_import_cost = grid_import_kw * import_tariff_val          # $/h (1-h interval)
            grid_export_revenue = grid_export_kw * export_tariff_step
            total_operating_cost = (
                grid_import_cost - grid_export_revenue + battery_degradation_cost
            )

            rows.append(
                {
                    "Timestamp": current_time,
                    "PV_Forecast_kW": pv0,
                    "Load_Forecast_kW": load0,
                    "Battery_Charge_kW": charge_kw,
                    "Battery_Discharge_kW": discharge_kw,
                    "Battery_SOC_kWh": soc_kwh,
                    "Battery_SOC_Percent": (soc_kwh / battery_cfg.battery_capacity_kwh) * 100.0,
                    "Grid_Import_kW": grid_import_kw,
                    "Grid_Export_kW": grid_export_kw,
                    "Solar_Curtailment_kW": curtailment_kw,
                    "Import_Tariff": import_tariff_val,
                    "Export_Tariff": export_tariff_step,
                    "Grid_Import_Cost": grid_import_cost,
                    "Grid_Export_Revenue": grid_export_revenue,
                    "Battery_Degradation_Cost": battery_degradation_cost,
                    "Total_Operating_Cost": total_operating_cost,
                }
            )

            # 6. Advance time ---------------------------------------------------
            current_time += pd.Timedelta(hours=1)

        # ---- Build schedule DataFrame ----------------------------------------
        schedule_df = pd.DataFrame(rows)

        # ---- Compute aggregate metrics ----------------------------------------
        metrics = self._compute_metrics(schedule_df, battery_cfg)

        return SimulationResult(
            schedule=schedule_df,
            metrics=metrics,
            solver_statuses=solver_statuses,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _update_soc(self, soc_kwh: float, charge_kw: float, discharge_kw: float) -> float:
        """Update battery SOC for one hourly timestep applying round-trip efficiency.

        Parameters
        ----------
        soc_kwh : float
            Current state-of-charge in kWh.
        charge_kw : float
            Charging power in kW (non-negative).
        discharge_kw : float
            Discharging power in kW (non-negative).

        Returns
        -------
        float
            Updated SOC in kWh, clamped to ``[soc_min_kwh, capacity_kwh]``.
        """
        battery_cfg = self.config
        dt = self.config.optimization.time_step_hours
        soc_new = (
            soc_kwh
            + battery_cfg.charge_efficiency * charge_kw * dt
            - discharge_kw * dt / battery_cfg.discharge_efficiency
        )

        # Clamp to physical bounds
        soc_min_kwh = battery_cfg.battery_capacity_kwh * battery_cfg.min_soc_percent / 100.0
        soc_max_kwh = battery_cfg.battery_capacity_kwh * battery_cfg.max_soc_percent / 100.0
        soc_new = max(soc_min_kwh, min(soc_max_kwh, soc_new))

        return soc_new

    def _get_import_tariffs(self, start_time: pd.Timestamp, horizon_hours: int) -> list:
        """Return a list of import tariffs ($/kWh) for each hour in the horizon.

        Parameters
        ----------
        start_time : pd.Timestamp
            UTC start of the horizon window.
        horizon_hours : int
            Number of hourly intervals.

        Returns
        -------
        list of float
            Import tariff for each hour, ordered chronologically.
        """
        tariff_cfg = self.config.tariff
        tariffs = []
        for h in range(horizon_hours):
            t = start_time + pd.Timedelta(hours=h)
            local_hour = self._local_hour(t)
            tariffs.append(get_import_tariff(local_hour, tariff_cfg))
        return tariffs

    @staticmethod
    def _local_hour(ts: pd.Timestamp) -> int:
        """Convert a UTC (or tz-aware) timestamp to Phoenix local hour."""
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        return ts.tz_convert(PHOENIX_TZ).hour

    def _compute_metrics(self, schedule_df: pd.DataFrame, battery_cfg) -> dict:
        """Compute aggregate KPIs from the executed schedule.

        Parameters
        ----------
        schedule_df : pd.DataFrame
            The completed schedule (one row per timestep).
        battery_cfg
            Battery configuration object with ``capacity_kwh``, ``soc_min_percent``,
            etc.

        Returns
        -------
        dict
            Dictionary of KPI names → values.
        """
        df = schedule_df

        total_pv = df["PV_Forecast_kW"].sum()          # kWh (1-h intervals)
        total_load = df["Load_Forecast_kW"].sum()
        total_import = df["Grid_Import_kW"].sum()
        total_export = df["Grid_Export_kW"].sum()
        total_charge = df["Battery_Charge_kW"].sum()
        total_discharge = df["Battery_Discharge_kW"].sum()
        total_curtailment = df["Solar_Curtailment_kW"].sum()
        total_cost = df["Total_Operating_Cost"].sum()

        # Solar self-consumption: PV energy used to meet load directly + via battery
        pv_to_load_direct = (df["PV_Forecast_kW"] - df["Battery_Charge_kW"] - df["Grid_Export_kW"] - df["Solar_Curtailment_kW"]).clip(lower=0).sum()
        pv_via_battery = total_discharge  # approximate: energy discharged that came from PV

        solar_self_consumption_pct = (
            ((pv_to_load_direct + pv_via_battery) / total_pv * 100.0)
            if total_pv > 0 else 0.0
        )
        solar_self_consumption_pct = min(solar_self_consumption_pct, 100.0)

        solar_utilization_pct = (
            ((total_pv - total_curtailment) / total_pv * 100.0)
            if total_pv > 0 else 100.0
        )

        # SOC violation count
        soc_min_kwh = battery_cfg.battery_capacity_kwh * battery_cfg.min_soc_percent / 100.0
        soc_violations = int(
            ((df["Battery_SOC_kWh"] < soc_min_kwh - 1e-6) |
             (df["Battery_SOC_kWh"] > battery_cfg.battery_capacity_kwh + 1e-6)).sum()
        )

        return {
            "total_grid_import_kwh": round(total_import, 4),
            "total_grid_export_kwh": round(total_export, 4),
            "total_electricity_cost": round(total_cost, 4),
            "solar_self_consumption_percent": round(solar_self_consumption_pct, 2),
            "solar_utilization_percent": round(solar_utilization_pct, 2),
            "total_curtailment_kwh": round(total_curtailment, 4),
            "total_battery_charge_kwh": round(total_charge, 4),
            "total_battery_discharge_kwh": round(total_discharge, 4),
            "battery_throughput_kwh": round((total_charge + total_discharge) / 2.0, 4),
            "soc_violations": soc_violations,
            "peak_grid_import_kw": round(float(df["Grid_Import_kW"].max()), 4),
            "grid_dependency_percent": round(
                (total_import / total_load * 100.0) if total_load > 0 else 0.0, 2
            ),
        }
