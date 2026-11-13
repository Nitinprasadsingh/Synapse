"""
visualization.py
----------------
Visualization module for the MicroGrid Battery Optimization system.

Generates matplotlib-based plots for PV forecasts, battery state, grid
interaction, curtailment, cost comparisons, and energy balance.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from battery_optimization.config import MicrogridConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
COLORS = {
    "pv": "#F4A261",
    "load": "#264653",
    "battery_charge": "#2A9D8F",
    "battery_discharge": "#E76F51",
    "grid_import": "#457B9D",
    "grid_export": "#1D3557",
    "curtailment": "#E9C46A",
}

# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------
_STYLE_CANDIDATES = ["seaborn-v0_8-whitegrid", "ggplot"]


def _apply_style() -> None:
    """Apply the best available matplotlib style."""
    available = plt.style.available
    for style in _STYLE_CANDIDATES:
        if style in available:
            plt.style.use(style)
            return
    # Fallback: use default with grid enabled
    plt.rcParams.update({"axes.grid": True, "grid.alpha": 0.4})


def _time_axis(ax: plt.Axes, schedule_df: pd.DataFrame) -> None:
    """Format the x-axis as readable timestamps."""
    timestamp_col = "Timestamp" if "Timestamp" in schedule_df else "timestamp"
    if timestamp_col in schedule_df.columns:
        timestamps = pd.to_datetime(schedule_df[timestamp_col])
        ax.set_xticks(range(len(timestamps)))
        # Show every 4th label to avoid crowding
        step = max(1, len(timestamps) // 6)
        labels = [
            ts.strftime("%H:%M") if i % step == 0 else ""
            for i, ts in enumerate(timestamps)
        ]
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    else:
        ax.set_xlabel("Time Step")


# ---------------------------------------------------------------------------
# Main visualizer class
# ---------------------------------------------------------------------------


class MicrogridVisualizer:
    """Generate and save matplotlib plots for MicroGrid optimization results."""

    def __init__(self, output_dir: str = "outputs/plots") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _save(self, fig: plt.Figure, filename: str) -> str:
        """Save *fig* to *output_dir/<filename>.png* at 150 DPI and close it."""
        path = self.output_dir / filename
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info("Saved plot: %s", path)
        return str(path)

    @staticmethod
    def _x_range(df: pd.DataFrame) -> range:
        return range(len(df))

    @staticmethod
    def _series(df: pd.DataFrame, name: str, default: float = 0.0) -> pd.Series:
        aliases = {
            "pv_forecast_kw": "PV_Forecast_kW",
            "load_forecast_kw": "Load_Forecast_kW",
            "battery_charge_kw": "Battery_Charge_kW",
            "battery_discharge_kw": "Battery_Discharge_kW",
            "battery_soc_kwh": "Battery_SOC_kWh",
            "battery_soc_percent": "Battery_SOC_Percent",
            "grid_import_kw": "Grid_Import_kW",
            "grid_export_kw": "Grid_Export_kW",
            "curtailment_kw": "Solar_Curtailment_kW",
        }
        column = name if name in df else aliases.get(name, name)
        if column in df:
            return df[column]
        return pd.Series(default, index=df.index, dtype=float)

    # ------------------------------------------------------------------
    # Time-series plots
    # ------------------------------------------------------------------

    def plot_pv_vs_load(self, schedule_df: pd.DataFrame, title_suffix: str = "") -> str:
        """Plot PV generation vs load forecast. Returns saved file path."""
        _apply_style()
        fig, ax = plt.subplots(figsize=(12, 5))

        x = self._x_range(schedule_df)
        pv_col = "pv_forecast_kw"
        load_col = "load_forecast_kw"

        pv = self._series(schedule_df, pv_col)
        load = self._series(schedule_df, load_col)

        ax.plot(x, pv, color=COLORS["pv"], linewidth=2, label="PV Generation (kW)", marker="o", markersize=3)
        ax.plot(x, load, color=COLORS["load"], linewidth=2, label="Load Forecast (kW)", marker="s", markersize=3)

        ax.fill_between(x, pv, alpha=0.15, color=COLORS["pv"])
        ax.fill_between(x, load, alpha=0.10, color=COLORS["load"])

        ax.set_title(f"PV Generation vs Load Forecast{title_suffix}", fontsize=13, fontweight="bold")
        ax.set_xlabel("Time")
        ax.set_ylabel("Power (kW)")
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.4)
        ax.yaxis.set_minor_locator(mticker.AutoMinorLocator())
        _time_axis(ax, schedule_df)

        fig.tight_layout()
        return self._save(fig, f"pv_vs_load{title_suffix}.png")

    def plot_battery_power(self, schedule_df: pd.DataFrame, title_suffix: str = "") -> str:
        """Plot battery charging/discharging power over time."""
        _apply_style()
        fig, ax = plt.subplots(figsize=(12, 5))

        x = self._x_range(schedule_df)
        power = self._series(schedule_df, "battery_charge_kw") - self._series(
            schedule_df, "battery_discharge_kw"
        )

        # Positive = charging (green), negative = discharging (red)
        charge = power.clip(lower=0)
        discharge = power.clip(upper=0)

        ax.bar(x, charge, color=COLORS["battery_charge"], label="Charging (kW)", alpha=0.85)
        ax.bar(x, discharge, color=COLORS["battery_discharge"], label="Discharging (kW)", alpha=0.85)
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")

        ax.set_title(f"Battery Power (Charge / Discharge){title_suffix}", fontsize=13, fontweight="bold")
        ax.set_xlabel("Time")
        ax.set_ylabel("Power (kW)  [+ = charging, − = discharging]")
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.4)
        _time_axis(ax, schedule_df)

        fig.tight_layout()
        return self._save(fig, f"battery_power{title_suffix}.png")

    def plot_battery_soc(
        self,
        schedule_df: pd.DataFrame,
        config: "MicrogridConfig",
        title_suffix: str = "",
    ) -> str:
        """Plot battery SOC with min/max SOC lines marked."""
        _apply_style()
        fig, ax = plt.subplots(figsize=(12, 5))

        x = self._x_range(schedule_df)
        soc = self._series(schedule_df, "battery_soc_kwh")

        # Determine units (kWh or %)
        if "Battery_SOC_kWh" in schedule_df.columns or "battery_soc_kwh" in schedule_df.columns:
            ylabel = "State of Charge (kWh)"
            try:
                min_soc = config.battery.min_soc_kwh
                max_soc = config.battery.max_soc_kwh
            except AttributeError:
                min_soc = max_soc = None
        else:
            ylabel = "State of Charge (%)"
            try:
                capacity = config.battery.capacity_kwh
                min_soc = (config.battery.min_soc_kwh / capacity) * 100
                max_soc = (config.battery.max_soc_kwh / capacity) * 100
            except AttributeError:
                min_soc = max_soc = None

        ax.plot(x, soc, color=COLORS["battery_charge"], linewidth=2.5, label="Battery SOC", marker="o", markersize=3)
        ax.fill_between(x, soc, alpha=0.15, color=COLORS["battery_charge"])

        if min_soc is not None:
            ax.axhline(min_soc, color="red", linestyle="--", linewidth=1.5, label=f"Min SOC ({min_soc:.1f})")
        if max_soc is not None:
            ax.axhline(max_soc, color="darkred", linestyle="--", linewidth=1.5, label=f"Max SOC ({max_soc:.1f})")

        ax.set_title(f"Battery State of Charge (SOC){title_suffix}", fontsize=13, fontweight="bold")
        ax.set_xlabel("Time")
        ax.set_ylabel(ylabel)
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.4)
        _time_axis(ax, schedule_df)

        fig.tight_layout()
        return self._save(fig, f"battery_soc{title_suffix}.png")

    def plot_grid_import_export(self, schedule_df: pd.DataFrame, title_suffix: str = "") -> str:
        """Plot grid import and export."""
        _apply_style()
        fig, ax = plt.subplots(figsize=(12, 5))

        x = self._x_range(schedule_df)
        grid_import = self._series(schedule_df, "grid_import_kw")
        grid_export = self._series(schedule_df, "grid_export_kw")

        ax.bar(x, grid_import, color=COLORS["grid_import"], label="Grid Import (kW)", alpha=0.85)
        ax.bar(x, -grid_export, color=COLORS["grid_export"], label="Grid Export (kW)", alpha=0.85)
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")

        ax.set_title(f"Grid Import / Export{title_suffix}", fontsize=13, fontweight="bold")
        ax.set_xlabel("Time")
        ax.set_ylabel("Power (kW)  [+ = import, − = export]")
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.4)
        _time_axis(ax, schedule_df)

        fig.tight_layout()
        return self._save(fig, f"grid_import_export{title_suffix}.png")

    def plot_curtailment(self, schedule_df: pd.DataFrame, title_suffix: str = "") -> str:
        """Plot solar curtailment."""
        _apply_style()
        fig, ax = plt.subplots(figsize=(12, 5))

        x = self._x_range(schedule_df)
        curtailment = self._series(schedule_df, "curtailment_kw")

        ax.bar(x, curtailment, color=COLORS["curtailment"], label="Solar Curtailment (kW)", alpha=0.85)
        ax.set_title(f"Solar Curtailment{title_suffix}", fontsize=13, fontweight="bold")
        ax.set_xlabel("Time")
        ax.set_ylabel("Curtailed Power (kW)")
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.4)
        _time_axis(ax, schedule_df)

        fig.tight_layout()
        return self._save(fig, f"curtailment{title_suffix}.png")

    # ------------------------------------------------------------------
    # Bar chart comparisons
    # ------------------------------------------------------------------

    def plot_cost_comparison(self, comparison_df: pd.DataFrame, title_suffix: str = "") -> str:
        """Plot total cost comparison bar chart across scenarios."""
        _apply_style()
        fig, ax = plt.subplots(figsize=(8, 5))

        scenarios = comparison_df.columns.tolist()
        metric = "total_electricity_cost"
        if metric not in comparison_df.index:
            raise ValueError(f"Comparison is missing metric {metric!r}")
        costs = comparison_df.loc[metric, scenarios].astype(float).tolist()

        bar_colors = [COLORS["grid_import"], COLORS["pv"], COLORS["battery_charge"],
                      COLORS["load"], COLORS["curtailment"]]
        colors_cycle = [bar_colors[i % len(bar_colors)] for i in range(len(scenarios))]

        bars = ax.bar(scenarios, costs, color=colors_cycle, alpha=0.85, edgecolor="white", linewidth=0.5)

        # Annotate bars with values
        for bar, val in zip(bars, costs):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(costs) * 0.01,
                f"${val:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        ax.set_title(f"Total Cost Comparison by Scenario{title_suffix}", fontsize=13, fontweight="bold")
        ax.set_xlabel("Scenario")
        ax.set_ylabel("Total Cost ($)")
        ax.grid(True, axis="y", alpha=0.4)
        plt.xticks(rotation=15, ha="right")

        fig.tight_layout()
        return self._save(fig, f"cost_comparison{title_suffix}.png")

    def plot_grid_dependency(self, comparison_df: pd.DataFrame, title_suffix: str = "") -> str:
        """Plot grid dependency % comparison bar chart."""
        _apply_style()
        fig, ax = plt.subplots(figsize=(8, 5))

        scenarios = comparison_df.columns.tolist()
        metric = "grid_dependency_percent"
        if metric not in comparison_df.index:
            raise ValueError(f"Comparison is missing metric {metric!r}")
        deps = comparison_df.loc[metric, scenarios].astype(float).tolist()

        bar_colors = [COLORS["grid_import"], COLORS["grid_export"], COLORS["battery_charge"],
                      COLORS["pv"], COLORS["load"]]
        colors_cycle = [bar_colors[i % len(bar_colors)] for i in range(len(scenarios))]

        bars = ax.bar(scenarios, deps, color=colors_cycle, alpha=0.85, edgecolor="white", linewidth=0.5)

        for bar, val in zip(bars, deps):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(deps) * 0.01,
                f"{val:.1f}%",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        ax.set_title(f"Grid Dependency Comparison by Scenario{title_suffix}", fontsize=13, fontweight="bold")
        ax.set_xlabel("Scenario")
        ax.set_ylabel("Grid Dependency (%)")
        ax.set_ylim(0, min(100, max(deps) * 1.15) if deps else 100)
        ax.grid(True, axis="y", alpha=0.4)
        plt.xticks(rotation=15, ha="right")

        fig.tight_layout()
        return self._save(fig, f"grid_dependency{title_suffix}.png")

    # ------------------------------------------------------------------
    # Energy balance
    # ------------------------------------------------------------------

    def plot_energy_balance(self, schedule_df: pd.DataFrame, title_suffix: str = "") -> str:
        """Plot stacked area chart showing energy sources and sinks."""
        _apply_style()
        fig, ax = plt.subplots(figsize=(12, 5))

        x = self._x_range(schedule_df)

        # Sources (positive contributions)
        pv = self._series(schedule_df, "pv_forecast_kw").fillna(0).values
        grid_import = self._series(schedule_df, "grid_import_kw").fillna(0).values
        batt_discharge = self._series(schedule_df, "battery_discharge_kw").fillna(0).values

        # Sinks (shown as negative / separate subplot if desired – here as reference lines)
        load = self._series(schedule_df, "load_forecast_kw").fillna(0).values

        # Stacked area: sources
        ax.stackplot(
            x,
            pv,
            grid_import,
            batt_discharge,
            labels=["PV Generation (kW)", "Grid Import (kW)", "Battery Discharge (kW)"],
            colors=[COLORS["pv"], COLORS["grid_import"], COLORS["battery_discharge"]],
            alpha=0.75,
        )

        # Overlay load demand as a line
        ax.plot(x, load, color=COLORS["load"], linewidth=2.5, linestyle="--", label="Load Demand (kW)", zorder=5)

        ax.set_title(f"Energy Balance (Sources & Load){title_suffix}", fontsize=13, fontweight="bold")
        ax.set_xlabel("Time")
        ax.set_ylabel("Power (kW)")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)
        _time_axis(ax, schedule_df)

        fig.tight_layout()
        return self._save(fig, f"energy_balance{title_suffix}.png")

    # ------------------------------------------------------------------
    # Convenience wrapper
    # ------------------------------------------------------------------

    def generate_all_plots(
        self,
        schedule_df: pd.DataFrame,
        comparison_df: pd.DataFrame,
        config: "MicrogridConfig",
    ) -> list[str]:
        """Generate all plots and return list of saved file paths."""
        paths: list[str] = []

        plotters = [
            lambda: self.plot_pv_vs_load(schedule_df),
            lambda: self.plot_battery_power(schedule_df),
            lambda: self.plot_battery_soc(schedule_df, config),
            lambda: self.plot_grid_import_export(schedule_df),
            lambda: self.plot_curtailment(schedule_df),
            lambda: self.plot_energy_balance(schedule_df),
        ]

        for fn in plotters:
            try:
                paths.append(fn())
            except Exception as exc:  # noqa: BLE001
                logger.warning("Plot generation skipped due to error: %s", exc)

        if comparison_df is not None and not comparison_df.empty:
            for fn in [
                lambda: self.plot_cost_comparison(comparison_df),
                lambda: self.plot_grid_dependency(comparison_df),
            ]:
                try:
                    paths.append(fn())
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Comparison plot skipped: %s", exc)

        logger.info("Generated %d plots in %s", len(paths), self.output_dir)
        return paths
