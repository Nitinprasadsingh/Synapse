"""
evaluation.py
-------------
Baseline scenario evaluators and comparison tools for the
MicroGrid Battery Optimization system.

Three scenarios are implemented:
  A) No battery  – PV feeds load directly; excess exported or curtailed.
  B) Rule-based  – Simple greedy charge-on-surplus / discharge-on-deficit logic.
  C) MPC         – Results produced externally by MPCScheduler (passed in for comparison).

A standalone ``validate_energy_balance`` function checks the energy balance
constraint at every timestep for any scenario schedule DataFrame.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Sequence

import numpy as np
import pandas as pd

from battery_optimization.tariff_utils import get_export_tariff, get_import_tariff
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from battery_optimization.config import MicrogridConfig

logger = logging.getLogger(__name__)

PHOENIX_TZ = ZoneInfo("America/Phoenix")

# Column order enforced across all scenario schedules
_SCHEDULE_COLUMNS = [
    "Timestamp",
    "PV_Forecast_kW",
    "Load_Forecast_kW",
    "Battery_Charge_kW",
    "Battery_Discharge_kW",
    "Battery_SOC_kWh",
    "Battery_SOC_Percent",
    "Grid_Import_kW",
    "Grid_Export_kW",
    "Solar_Curtailment_kW",
    "Import_Tariff",
    "Export_Tariff",
    "Grid_Import_Cost",
    "Grid_Export_Revenue",
    "Battery_Degradation_Cost",
    "Total_Operating_Cost",
]


# ---------------------------------------------------------------------------
# Standalone utility
# ---------------------------------------------------------------------------


def validate_energy_balance(
    schedule_df: pd.DataFrame,
    tolerance: float = 1e-4,
) -> tuple[bool, float, pd.DataFrame]:
    """Check the energy balance at every timestep in a schedule DataFrame.

    The balance equation (all quantities in kW, 1-hour intervals, so kWh = kW):

        PV + Grid_Import + Battery_Discharge
        == Load + Battery_Charge + Grid_Export + Solar_Curtailment

    Parameters
    ----------
    schedule_df : pd.DataFrame
        Schedule with the standard columns produced by any scenario evaluator.
    tolerance : float, optional
        Absolute residual threshold (kW) below which a timestep is considered balanced.
        Default is 1e-4.

    Returns
    -------
    is_valid : bool
        True if **all** timesteps are within tolerance.
    max_residual : float
        Maximum absolute residual across all timesteps.
    violations_df : pd.DataFrame
        Sub-DataFrame of rows whose absolute residual exceeds *tolerance*.
        Empty when is_valid is True.
    """
    df = schedule_df.copy()

    lhs = (
        df["PV_Forecast_kW"]
        + df["Grid_Import_kW"]
        + df["Battery_Discharge_kW"]
    )
    rhs = (
        df["Load_Forecast_kW"]
        + df["Battery_Charge_kW"]
        + df["Grid_Export_kW"]
        + df["Solar_Curtailment_kW"]
    )
    residual = (lhs - rhs).abs()

    max_residual = float(residual.max())
    is_valid = bool(max_residual <= tolerance)
    violations_mask = residual > tolerance
    violations_df = df[violations_mask].copy()
    violations_df["Energy_Balance_Residual_kW"] = residual[violations_mask]

    return is_valid, max_residual, violations_df


# ---------------------------------------------------------------------------
# Helper: local Phoenix hour from a Timestamp
# ---------------------------------------------------------------------------


def _local_hour(ts: pd.Timestamp) -> int:
    """Return the America/Phoenix local hour from a timezone-aware timestamp."""
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.tz_convert(PHOENIX_TZ).hour


# ---------------------------------------------------------------------------
# BaselineEvaluator
# ---------------------------------------------------------------------------


class BaselineEvaluator:
    """Evaluate and compare energy-management scenarios.

    Parameters
    ----------
    config : MicrogridConfig
        System-wide configuration (battery, tariff, etc.).
    """

    def __init__(self, config: "MicrogridConfig") -> None:
        self.config = config

    # ------------------------------------------------------------------
    # Scenario A – No battery
    # ------------------------------------------------------------------

    def scenario_a_no_battery(
        self,
        pv_forecast_kw: Sequence[float],
        load_forecast_kw: Sequence[float],
        import_tariffs: Sequence[float],
        export_tariff: float,
        allow_export: bool = True,
        timestamps: Optional[Sequence[pd.Timestamp]] = None,
    ) -> dict:
        """Simulate the system with **no battery** present.

        Energy flows
        ------------
        - PV supplies load directly for each hour.
        - Surplus PV (pv > load):
          - Exported to grid if *allow_export* is True.
          - Otherwise curtailed.
        - Deficit (load > pv): imported from grid.

        Parameters
        ----------
        pv_forecast_kw : sequence of float
            Hourly PV generation forecast (kW).
        load_forecast_kw : sequence of float
            Hourly load forecast (kW).
        import_tariffs : sequence of float
            Import tariff ($/kWh) for each hour.
        export_tariff : float
            Flat export tariff ($/kWh).
        allow_export : bool, optional
            Whether surplus PV can be exported (default True).
        timestamps : sequence of pd.Timestamp, optional
            Timestamps for each interval; auto-generated if None.

        Returns
        -------
        dict
            ``{"schedule": pd.DataFrame, "metrics": dict, "label": str}``.
        """
        n = len(pv_forecast_kw)
        if timestamps is None:
            timestamps = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")

        rows = []
        for i in range(n):
            pv = float(pv_forecast_kw[i])
            load = float(load_forecast_kw[i])
            imp_tariff = float(import_tariffs[i])
            exp_tariff = export_tariff

            surplus = max(0.0, pv - load)
            deficit = max(0.0, load - pv)

            grid_import = deficit
            if allow_export:
                grid_export = surplus
                curtailment = 0.0
            else:
                grid_export = 0.0
                curtailment = surplus

            grid_import_cost = grid_import * imp_tariff
            grid_export_revenue = grid_export * exp_tariff
            total_cost = grid_import_cost - grid_export_revenue

            rows.append(
                {
                    "Timestamp": timestamps[i],
                    "PV_Forecast_kW": pv,
                    "Load_Forecast_kW": load,
                    "Battery_Charge_kW": 0.0,
                    "Battery_Discharge_kW": 0.0,
                    "Battery_SOC_kWh": 0.0,
                    "Battery_SOC_Percent": 0.0,
                    "Grid_Import_kW": grid_import,
                    "Grid_Export_kW": grid_export,
                    "Solar_Curtailment_kW": curtailment,
                    "Import_Tariff": imp_tariff,
                    "Export_Tariff": exp_tariff,
                    "Grid_Import_Cost": grid_import_cost,
                    "Grid_Export_Revenue": grid_export_revenue,
                    "Battery_Degradation_Cost": 0.0,
                    "Total_Operating_Cost": total_cost,
                }
            )

        schedule_df = pd.DataFrame(rows, columns=_SCHEDULE_COLUMNS)
        metrics = self._compute_metrics(schedule_df, label="A_NoBattery")
        return {"schedule": schedule_df, "metrics": metrics, "label": "A_NoBattery"}

    # ------------------------------------------------------------------
    # Scenario B – Rule-based battery
    # ------------------------------------------------------------------

    def scenario_b_rule_based(
        self,
        pv_forecast_kw: Sequence[float],
        load_forecast_kw: Sequence[float],
        import_tariffs: Sequence[float],
        export_tariff: float,
        initial_soc_percent: Optional[float] = None,
        allow_export: bool = True,
        timestamps: Optional[Sequence[pd.Timestamp]] = None,
    ) -> dict:
        """Simulate a simple rule-based battery controller.

        Rules (applied each hour in order)
        -----------------------------------
        1. Compute net power = PV − Load.
        2. **If net > 0 (surplus PV)**:
           - Charge battery: ``charge = min(surplus, max_charge_kw, room_in_battery_kwh)``
           - Remaining surplus after charging:
             - Export if *allow_export*, else curtail.
        3. **If net < 0 (deficit)**:
           - Discharge battery: ``discharge = min(|deficit|, max_discharge_kw, available_kwh)``
           - Remaining deficit after discharging: import from grid.
        4. SOC bounds are enforced at all times.

        Parameters
        ----------
        pv_forecast_kw : sequence of float
        load_forecast_kw : sequence of float
        import_tariffs : sequence of float
        export_tariff : float
        initial_soc_percent : float, optional
            Starting SOC as % of usable capacity.
        allow_export : bool, optional
            Whether surplus can be exported to the grid.
        timestamps : sequence of pd.Timestamp, optional

        Returns
        -------
        dict
            ``{"schedule": pd.DataFrame, "metrics": dict, "label": str}``.
        """
        battery_cfg = self.config.battery
        n = len(pv_forecast_kw)

        if timestamps is None:
            timestamps = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")

        # Battery parameters
        capacity_kwh: float = battery_cfg.capacity_kwh
        soc_min_percent: float = getattr(battery_cfg, "soc_min_percent", 10.0)
        soc_min_kwh: float = capacity_kwh * soc_min_percent / 100.0
        max_charge_kw: float = getattr(battery_cfg, "max_charge_kw", capacity_kwh * 0.5)
        max_discharge_kw: float = getattr(battery_cfg, "max_discharge_kw", capacity_kwh * 0.5)
        eta: float = getattr(battery_cfg, "round_trip_efficiency", 0.9) ** 0.5
        degradation_cost_per_kwh: float = getattr(battery_cfg, "degradation_cost_per_kwh", 0.0)

        if initial_soc_percent is None:
            initial_soc_percent = getattr(battery_cfg, "initial_soc_percent", 50.0)
        soc_kwh: float = initial_soc_percent / 100.0 * capacity_kwh

        rows = []
        for i in range(n):
            pv = float(pv_forecast_kw[i])
            load = float(load_forecast_kw[i])
            imp_tariff = float(import_tariffs[i])
            exp_tariff = export_tariff

            net = pv - load  # positive = surplus, negative = deficit

            charge_kw = 0.0
            discharge_kw = 0.0
            curtailment = 0.0

            if net >= 0.0:
                # Surplus: attempt to charge battery
                surplus = net
                room_kwh = capacity_kwh - soc_kwh          # space left in battery
                # Charge: limited by room (accounting for efficiency), max charge rate
                charge_energy_deliverable = room_kwh / eta if eta > 0 else room_kwh
                charge_kw = min(surplus, max_charge_kw, charge_energy_deliverable)
                charge_kw = max(0.0, charge_kw)

                # Update SOC with this charge
                soc_kwh = min(capacity_kwh, soc_kwh + eta * charge_kw * 1.0)

                remaining_surplus = surplus - charge_kw
                if allow_export:
                    grid_export = remaining_surplus
                    curtailment = 0.0
                else:
                    grid_export = 0.0
                    curtailment = remaining_surplus

                grid_import = 0.0

            else:
                # Deficit: attempt to discharge battery
                deficit = -net
                available_kwh = soc_kwh - soc_min_kwh       # energy available above minimum
                discharge_energy_deliverable = available_kwh * eta if eta > 0 else available_kwh
                discharge_kw = min(deficit, max_discharge_kw, discharge_energy_deliverable)
                discharge_kw = max(0.0, discharge_kw)

                # Update SOC with this discharge
                soc_kwh = max(soc_min_kwh, soc_kwh - discharge_kw / eta)

                remaining_deficit = deficit - discharge_kw
                grid_import = remaining_deficit
                grid_export = 0.0
                curtailment = 0.0

            # Clamp SOC safety check
            soc_kwh = max(soc_min_kwh, min(capacity_kwh, soc_kwh))
            soc_pct = soc_kwh / capacity_kwh * 100.0

            # Costs
            throughput_kwh = (charge_kw + discharge_kw) * 0.5
            battery_degradation_cost = throughput_kwh * degradation_cost_per_kwh
            grid_import_cost = grid_import * imp_tariff
            grid_export_revenue = grid_export * exp_tariff
            total_cost = grid_import_cost - grid_export_revenue + battery_degradation_cost

            rows.append(
                {
                    "Timestamp": timestamps[i],
                    "PV_Forecast_kW": pv,
                    "Load_Forecast_kW": load,
                    "Battery_Charge_kW": charge_kw,
                    "Battery_Discharge_kW": discharge_kw,
                    "Battery_SOC_kWh": soc_kwh,
                    "Battery_SOC_Percent": soc_pct,
                    "Grid_Import_kW": grid_import,
                    "Grid_Export_kW": grid_export,
                    "Solar_Curtailment_kW": curtailment,
                    "Import_Tariff": imp_tariff,
                    "Export_Tariff": exp_tariff,
                    "Grid_Import_Cost": grid_import_cost,
                    "Grid_Export_Revenue": grid_export_revenue,
                    "Battery_Degradation_Cost": battery_degradation_cost,
                    "Total_Operating_Cost": total_cost,
                }
            )

        schedule_df = pd.DataFrame(rows, columns=_SCHEDULE_COLUMNS)
        metrics = self._compute_metrics(schedule_df, label="B_RuleBased")
        return {"schedule": schedule_df, "metrics": metrics, "label": "B_RuleBased"}

    # ------------------------------------------------------------------
    # Scenario comparison
    # ------------------------------------------------------------------

    def compare_scenarios(
        self,
        scenario_a: dict,
        scenario_b: dict,
        scenario_c_mpc: dict,
    ) -> pd.DataFrame:
        """Build a side-by-side comparison of all three scenarios.

        Parameters
        ----------
        scenario_a : dict
            Output of :meth:`scenario_a_no_battery`.
        scenario_b : dict
            Output of :meth:`scenario_b_rule_based`.
        scenario_c_mpc : dict
            Dict with keys ``"metrics"`` and ``"label"`` produced by or
            converted from an :class:`~battery_optimization.scheduler.SimulationResult`.
            If a ``SimulationResult`` is passed directly its ``.metrics`` and
            a label ``"C_MPC"`` are used automatically.

        Returns
        -------
        pd.DataFrame
            Metrics as rows, scenario names as columns, plus two
            ``%_Improvement_vs_*`` columns showing MPC gains over baselines.
        """
        # Accept SimulationResult instances directly
        from battery_optimization.scheduler import SimulationResult  # lazy import
        if isinstance(scenario_c_mpc, SimulationResult):
            scenario_c_mpc = {
                "metrics": scenario_c_mpc.metrics,
                "label": "C_MPC",
            }

        label_a = scenario_a.get("label", "A_NoBattery")
        label_b = scenario_b.get("label", "B_RuleBased")
        label_c = scenario_c_mpc.get("label", "C_MPC")

        metrics_a = scenario_a["metrics"]
        metrics_b = scenario_b["metrics"]
        metrics_c = scenario_c_mpc["metrics"]

        # Union of all metric keys
        all_keys = list(
            dict.fromkeys(list(metrics_a.keys()) + list(metrics_b.keys()) + list(metrics_c.keys()))
        )

        data = {
            label_a: {k: metrics_a.get(k, float("nan")) for k in all_keys},
            label_b: {k: metrics_b.get(k, float("nan")) for k in all_keys},
            label_c: {k: metrics_c.get(k, float("nan")) for k in all_keys},
        }
        comparison = pd.DataFrame(data, index=all_keys)
        comparison.index.name = "Metric"

        # Percentage improvement of MPC vs baselines (for cost/import metrics lower is better;
        # for self-consumption / utilization higher is better).
        _lower_better = {
            "total_grid_import_kwh",
            "total_electricity_cost",
            "total_curtailment_kwh",
            "battery_throughput_kwh",
            "soc_violations",
            "peak_grid_import_kw",
            "grid_dependency_percent",
        }
        _higher_better = {
            "total_grid_export_kwh",
            "solar_self_consumption_percent",
            "solar_utilization_percent",
            "total_battery_charge_kwh",
            "total_battery_discharge_kwh",
        }

        pct_vs_a = {}
        pct_vs_b = {}
        for k in all_keys:
            val_a = metrics_a.get(k, float("nan"))
            val_b = metrics_b.get(k, float("nan"))
            val_c = metrics_c.get(k, float("nan"))

            if k in _lower_better:
                # Improvement = (baseline - mpc) / baseline * 100
                pct_vs_a[k] = (
                    (val_a - val_c) / val_a * 100.0 if val_a and not pd.isna(val_a) else float("nan")
                )
                pct_vs_b[k] = (
                    (val_b - val_c) / val_b * 100.0 if val_b and not pd.isna(val_b) else float("nan")
                )
            elif k in _higher_better:
                # Improvement = (mpc - baseline) / baseline * 100
                pct_vs_a[k] = (
                    (val_c - val_a) / val_a * 100.0 if val_a and not pd.isna(val_a) else float("nan")
                )
                pct_vs_b[k] = (
                    (val_c - val_b) / val_b * 100.0 if val_b and not pd.isna(val_b) else float("nan")
                )
            else:
                pct_vs_a[k] = float("nan")
                pct_vs_b[k] = float("nan")

        comparison[f"%_Improvement_MPC_vs_{label_a}"] = pd.Series(pct_vs_a)
        comparison[f"%_Improvement_MPC_vs_{label_b}"] = pd.Series(pct_vs_b)

        return comparison

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_metrics(self, schedule_df: pd.DataFrame, label: str = "") -> dict:
        """Compute standard aggregate KPIs from a schedule DataFrame.

        Parameters
        ----------
        schedule_df : pd.DataFrame
            Schedule with the standard column set.
        label : str, optional
            Scenario label (unused in computation; kept for logging).

        Returns
        -------
        dict
            KPI name → value.
        """
        df = schedule_df
        battery_cfg = self.config.battery

        total_pv = df["PV_Forecast_kW"].sum()
        total_load = df["Load_Forecast_kW"].sum()
        total_import = df["Grid_Import_kW"].sum()
        total_export = df["Grid_Export_kW"].sum()
        total_charge = df["Battery_Charge_kW"].sum()
        total_discharge = df["Battery_Discharge_kW"].sum()
        total_curtailment = df["Solar_Curtailment_kW"].sum()
        total_cost = df["Total_Operating_Cost"].sum()

        # Solar self-consumption: PV energy consumed on-site (directly + via battery)
        pv_to_load_direct = (
            df["PV_Forecast_kW"]
            - df["Battery_Charge_kW"]
            - df["Grid_Export_kW"]
            - df["Solar_Curtailment_kW"]
        ).clip(lower=0.0).sum()
        solar_self_consumption_pct = (
            min((pv_to_load_direct + total_discharge) / total_pv * 100.0, 100.0)
            if total_pv > 0 else 0.0
        )

        solar_utilization_pct = (
            (total_pv - total_curtailment) / total_pv * 100.0
            if total_pv > 0 else 100.0
        )

        # SOC violations (only relevant when battery is present)
        capacity_kwh = battery_cfg.capacity_kwh
        soc_min_kwh = capacity_kwh * getattr(battery_cfg, "soc_min_percent", 10.0) / 100.0
        soc_col = df["Battery_SOC_kWh"]
        # For no-battery scenario all SOC values are 0 – count as 0 violations
        has_battery = (soc_col != 0).any()
        if has_battery:
            soc_violations = int(
                ((soc_col < soc_min_kwh - 1e-6) | (soc_col > capacity_kwh + 1e-6)).sum()
            )
        else:
            soc_violations = 0

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
                total_import / total_load * 100.0 if total_load > 0 else 0.0, 2
            ),
        }
