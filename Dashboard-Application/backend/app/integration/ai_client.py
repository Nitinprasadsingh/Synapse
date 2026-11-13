from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx

from app.schemas.battery import BatteryScheduleResponse, BatteryScheduleStepSchema
from app.schemas.forecast import (
    ForecastPoint,
    LoadForecastResponse,
    LoadForecastSummary,
    PVForecastResponse,
)

logger = logging.getLogger(__name__)


class AIServiceError(RuntimeError):
    """Raised when the AI service returns an invalid or unsuccessful response."""


class AIServiceClient:
    """HTTP adapter for the existing Python forecasting and optimization API."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        start_time: str | None = None,
    ) -> None:
        self.base_url = (
            base_url or os.getenv("AI_SERVICE_URL", "http://127.0.0.1:8100")
        ).rstrip("/")
        self.timeout = timeout or float(os.getenv("AI_SERVICE_TIMEOUT_SECONDS", "30.0"))
        self.start_time = start_time or os.getenv(
            "AI_SIMULATION_START_TIME", "2019-01-08T00:00:00Z"
        )

    def simulate(self, horizon_hours: int = 24) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{self.base_url}/optimization/simulate",
                json={"start_time": self.start_time, "horizon_hours": horizon_hours},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AIServiceError(f"AI service simulation failed: {exc}") from exc
        if not isinstance(payload, dict) or not payload.get("schedule"):
            raise AIServiceError("AI service returned an empty simulation schedule")
        return payload

    def to_dashboard_state(
        self, payload: dict[str, Any], capacity_kwh: float
    ) -> dict[str, Any]:
        schedule = payload["schedule"]
        if not isinstance(schedule, list):
            raise AIServiceError("AI service schedule is not a list")
        if len(schedule) == 0:
            raise AIServiceError("AI service schedule contains no steps")

        steps: list[BatteryScheduleStepSchema] = []
        pv_points: list[ForecastPoint] = []
        load_points: list[ForecastPoint] = []
        previous_soc = float(schedule[0].get("Battery_SOC_Percent", 0.0))
        for index, row in enumerate(schedule):
            charge = float(row.get("Battery_Charge_kW", 0.0))
            discharge = float(row.get("Battery_Discharge_kW", 0.0))
            action = "CHARGE" if charge > 1e-6 else "DISCHARGE" if discharge > 1e-6 else "IDLE"
            power = charge if action == "CHARGE" else discharge
            soc_after = float(row.get("Battery_SOC_Percent", 0.0))
            timestamp = row["Timestamp"]
            pv = float(row["PV_Forecast_kW"])
            load = float(row["Load_Forecast_kW"])
            pv_points.append(
                ForecastPoint(timestamp=timestamp, horizon_hour=index, value_kw=pv,
                              is_historical=False)
            )
            load_points.append(
                ForecastPoint(timestamp=timestamp, horizon_hour=index, value_kw=load,
                              is_historical=False)
            )
            steps.append(
                BatteryScheduleStepSchema(
                    step_index=index,
                    timestamp=timestamp,
                    pv_forecast_kw=pv,
                    load_forecast_kw=load,
                    action=action,
                    battery_power_kw=power,
                    soc_before=previous_soc,
                    soc_after=soc_after,
                    grid_import_kw=float(row.get("Grid_Import_kW", 0.0)),
                    grid_export_kw=float(row.get("Grid_Export_kW", 0.0)),
                    step_cost=float(row.get("Total_Operating_Cost", 0.0)),
                )
            )
            previous_soc = soc_after

        generated_at = datetime.now(timezone.utc)
        total_cost = float(payload.get("metrics", {}).get("total_electricity_cost", 0.0))
        first_timestamp = pv_points[0].timestamp
        return {
            "pv_forecast": PVForecastResponse(
                model_id="open-meteo-xgboost-v1",
                model_name="Open-Meteo Operational XGBoost",
                forecast_timestamp=first_timestamp,
                horizon_hours=len(pv_points),
                is_simulated=False,
                unit="kW",
                status_label="LIVE MODEL OUTPUT",
                forecast_points=pv_points,
                historical_points=[],
            ),
            "load_forecast": LoadForecastResponse(
                model_id="county-load-xgboost-v1",
                model_name="County Load XGBoost (scaled representative profile)",
                forecast_timestamp=first_timestamp,
                horizon_hours=len(load_points),
                is_simulated=False,
                unit="kW",
                status_label="LIVE MODEL OUTPUT",
                summary=LoadForecastSummary(
                    expected_peak_kw=max(p.value_kw for p in load_points),
                    expected_min_kw=min(p.value_kw for p in load_points),
                    average_demand_kw=sum(p.value_kw for p in load_points) / len(load_points),
                    total_energy_kwh=sum(p.value_kw for p in load_points),
                ),
                forecast_points=load_points,
                historical_points=[],
            ),
            "schedule": BatteryScheduleResponse(
                schedule_id=f"AI-{generated_at.strftime('%Y%m%d%H%M%S')}",
                generated_at=generated_at,
                status="GENERATED",
                total_cost=total_cost,
                algorithm="Pyomo HiGHS MPC",
                is_simulated=False,
                status_label="LIVE MODEL OUTPUT",
                notes="Open-Meteo PV and scaled county-load forecasts optimized by the AI service.",
                steps=steps,
            ),
        }
