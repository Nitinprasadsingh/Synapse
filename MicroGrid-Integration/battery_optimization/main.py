"""Command-line pipeline for the offline microgrid demonstration."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from battery_optimization.config import load_config
from battery_optimization.evaluation import BaselineEvaluator, validate_energy_balance
from battery_optimization.forecast_integration import ForecastIntegrationService
from battery_optimization.optimizer import BatteryOptimizer
from battery_optimization.scheduler import MPCScheduler
from battery_optimization.visualization import MicrogridVisualizer


def optimizer_config(config) -> dict:
    return {
        "MAX_CHARGE_POWER_KW": config.max_charge_power_kw,
        "MAX_DISCHARGE_POWER_KW": config.max_discharge_power_kw,
        "BATTERY_CAPACITY_KWH": config.battery_capacity_kwh,
        "MIN_SOC_PERCENT": config.min_soc_percent / 100.0,
        "MAX_SOC_PERCENT": config.max_soc_percent / 100.0,
        "CHARGE_EFFICIENCY": config.charge_efficiency,
        "DISCHARGE_EFFICIENCY": config.discharge_efficiency,
        "DEGRADATION_COST_PER_KWH": config.tariff.battery_degradation_cost_per_kwh,
        "GRID_IMPORT_LIMIT_KW": config.grid_import_limit_kw,
        "GRID_EXPORT_LIMIT_KW": config.grid_export_limit_kw,
        "EXPORT_TARIFF": config.tariff.export_tariff,
        "CURTAILMENT_PENALTY": config.tariff.curtailment_penalty_per_kwh,
        "OPTIMIZATION_HORIZON_HOURS": config.optimization.horizon_hours,
        "DT": config.optimization.time_step_hours,
        "IMPORT_TARIFF": config.tariff.import_tariff_offpeak,
    }


def run_pipeline(start_time: str = "2019-01-08T00:00:00Z", simulation_hours: int = 24):
    print("Loading configuration and trained forecasting models...", flush=True)
    config = load_config()
    service = ForecastIntegrationService(config)
    optimizer = BatteryOptimizer(optimizer_config(config))
    scheduler = MPCScheduler(optimizer, service, config)
    print(
        f"Running {simulation_hours}-hour MPC simulation with HiGHS...",
        flush=True,
    )
    result = scheduler.run_simulation(pd.Timestamp(start_time), simulation_hours)

    output_dir = Path(__file__).resolve().parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    print("Writing schedule, metrics, comparisons, and plots...", flush=True)
    result.schedule.to_csv(output_dir / "optimized_schedule.csv", index=False)
    (output_dir / "optimization_metrics.json").write_text(
        json.dumps(result.metrics, indent=2), encoding="utf-8"
    )
    evaluator = BaselineEvaluator(config)
    pv = result.schedule["PV_Forecast_kW"].tolist()
    load = result.schedule["Load_Forecast_kW"].tolist()
    tariffs = result.schedule["Import_Tariff"].tolist()
    timestamps = pd.to_datetime(result.schedule["Timestamp"]).tolist()
    no_battery = evaluator.scenario_a_no_battery(
        pv, load, tariffs, config.tariff.export_tariff,
        allow_export=config.allow_grid_export, timestamps=timestamps
    )
    rule_based = evaluator.scenario_b_rule_based(
        pv, load, tariffs, config.tariff.export_tariff,
        initial_soc_percent=config.initial_soc_percent,
        allow_export=config.allow_grid_export, timestamps=timestamps
    )
    comparison = evaluator.compare_scenarios(
        no_battery, rule_based, {"metrics": result.metrics, "label": "C_MPC"}
    )
    comparison.to_csv(output_dir / "baseline_comparison.csv")
    MicrogridVisualizer(output_dir / "plots").generate_all_plots(
        result.schedule, comparison, config
    )
    valid, residual, _ = validate_energy_balance(result.schedule)
    (output_dir / "optimization_report.md").write_text(
        "# Optimization Report\n\n"
        f"- Energy balance valid: **{valid}** (max residual {residual:.3g} kW)\n"
        f"- Load profile: **SIMULATED** county load scaled to a representative microgrid\n"
        f"- Solver calls: {len(result.solver_statuses)}\n",
        encoding="utf-8",
    )
    print("Completed successfully.", flush=True)
    print(f"Outputs: {output_dir}", flush=True)
    print(
        f"Total operating cost: ${result.metrics['total_electricity_cost']:.2f}; "
        f"grid import: {result.metrics['total_grid_import_kwh']:.2f} kWh",
        flush=True,
    )
    return result


if __name__ == "__main__":
    run_pipeline()
