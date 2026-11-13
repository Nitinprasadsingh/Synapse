"""FastAPI interface for the microgrid optimizer."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from battery_optimization.config import MicrogridConfig
from battery_optimization.evaluation import BaselineEvaluator
from battery_optimization.forecast_integration import ForecastIntegrationService
from battery_optimization.main import optimizer_config
from battery_optimization.optimizer import BatteryOptimizer
from battery_optimization.scheduler import MPCScheduler

app = FastAPI(title="MicroGrid Optimization API", version="0.1.0")
config = MicrogridConfig()
service = ForecastIntegrationService(config)
optimizer = BatteryOptimizer(optimizer_config(config))
latest_result = None
latest_baselines: dict[str, Any] = {}
latest_status: dict[str, Any] = {"state": "idle", "solver_statuses": []}


class RunRequest(BaseModel):
    start_time: datetime
    horizon_hours: int = Field(default=24, gt=0, le=168)


class ConfigUpdate(BaseModel):
    """Validated subset of runtime settings that can be changed through the API."""

    pv_capacity_kw: float | None = Field(default=None, gt=0)
    battery_capacity_kwh: float | None = Field(default=None, gt=0)
    initial_soc_percent: float | None = Field(default=None, ge=0, le=100)
    min_soc_percent: float | None = Field(default=None, ge=0, le=100)
    max_soc_percent: float | None = Field(default=None, ge=0, le=100)
    max_charge_power_kw: float | None = Field(default=None, gt=0)
    max_discharge_power_kw: float | None = Field(default=None, gt=0)
    allow_grid_export: bool | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "solver": "HiGHS"}


@app.get("/config")
def get_config() -> dict:
    return config.to_dict()


@app.post("/config")
def update_config(update: ConfigUpdate) -> dict:
    global config, service, optimizer
    values = update.model_dump(exclude_none=True)
    candidate = {
        key: getattr(config, key)
        for key in MicrogridConfig.__dataclass_fields__
        if key not in {"tariff", "optimization", "scaling"}
    }
    candidate.update(values)
    new_config = MicrogridConfig(
        **candidate,
        tariff=config.tariff,
        optimization=config.optimization,
        scaling=config.scaling,
    )
    new_config.validate()
    config = new_config
    service = ForecastIntegrationService(config)
    optimizer = BatteryOptimizer(optimizer_config(config))
    return config.to_dict()


@app.post("/forecast/generate")
def generate_forecast(request: RunRequest) -> dict:
    try:
        return service.get_forecast(pd.Timestamp(request.start_time), request.horizon_hours)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/optimization/simulate")
def simulate(request: RunRequest) -> dict:
    global latest_result, latest_baselines, latest_status
    latest_status = {"state": "running", "solver_statuses": []}
    try:
        scheduler = MPCScheduler(optimizer, service, config)
        latest_result = scheduler.run_simulation(
            pd.Timestamp(request.start_time), request.horizon_hours
        )
        evaluator = BaselineEvaluator(config)
        pv = latest_result.schedule["PV_Forecast_kW"].tolist()
        load = latest_result.schedule["Load_Forecast_kW"].tolist()
        tariffs = latest_result.schedule["Import_Tariff"].tolist()
        timestamps = pd.to_datetime(latest_result.schedule["Timestamp"]).tolist()
        no_battery = evaluator.scenario_a_no_battery(
            pv, load, tariffs, config.tariff.export_tariff,
            config.allow_grid_export, timestamps,
        )
        rule_based = evaluator.scenario_b_rule_based(
            pv, load, tariffs, config.tariff.export_tariff,
            config.initial_soc_percent, config.allow_grid_export, timestamps,
        )
        latest_baselines = {
            "A_NoBattery": no_battery["metrics"],
            "B_RuleBased": rule_based["metrics"],
            "C_MPC": latest_result.metrics,
        }
        latest_status = {
            "state": "complete",
            "solver_statuses": latest_result.solver_statuses,
            "simulation_hours": request.horizon_hours,
        }
        return {
            "metrics": latest_result.metrics,
            "schedule": latest_result.schedule.to_dict(orient="records"),
            "solver_statuses": latest_result.solver_statuses,
        }
    except Exception as exc:
        latest_status = {"state": "failed", "error": str(exc)}
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/optimization/run")
def run_optimization(request: RunRequest) -> dict:
    """Run one full forecast-horizon optimization without MPC execution."""
    try:
        horizon = config.optimization.horizon_hours
        if request.horizon_hours != horizon:
            raise ValueError(
                f"One-shot optimization requires horizon_hours={horizon}; "
                "use /optimization/simulate for a longer run."
            )
        forecast = service.get_forecast(pd.Timestamp(request.start_time), horizon)
        start = pd.Timestamp(request.start_time)
        if start.tzinfo is None:
            start = start.tz_localize("UTC")
        timestamps = pd.date_range(start, periods=horizon, freq="h")
        import_tariffs = [
            config.tariff.import_tariff_peak
            if timestamp.tz_convert(config.timezone).hour in config.tariff.peak_hours
            else config.tariff.import_tariff_offpeak
            for timestamp in timestamps
        ]
        result = optimizer.optimize(
            forecast["pv_kw"], forecast["load_kw"],
            config.battery_capacity_kwh * config.initial_soc_percent / 100.0,
            import_tariffs=import_tariffs,
            allow_export=config.allow_grid_export,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/optimization/schedule")
def schedule() -> dict:
    if latest_result is None:
        raise HTTPException(status_code=404, detail="No optimization has been run")
    return {"schedule": latest_result.schedule.to_dict(orient="records")}


@app.get("/optimization/metrics")
def metrics() -> dict:
    if latest_result is None:
        raise HTTPException(status_code=404, detail="No optimization has been run")
    return latest_result.metrics


@app.get("/optimization/baselines")
def baselines() -> dict:
    if not latest_baselines:
        raise HTTPException(status_code=404, detail="No simulation has been run")
    return latest_baselines


@app.get("/optimization/status")
def status() -> dict:
    return latest_status
