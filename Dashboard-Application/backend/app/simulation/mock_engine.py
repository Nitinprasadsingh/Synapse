from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.forecasting.mock_provider import MockPVForecastProvider, MockLoadForecastProvider
from app.optimization.mock_provider import MockBatteryOptimizationProvider
from app.models.battery import BatteryConfiguration
from app.models.grid import GridConfiguration
from app.models.settings import SystemSetting
from app.schemas.battery import BatteryConfigSchema
from app.schemas.grid import GridConfigSchema
from app.schemas.dashboard import (
    OverviewKpisResponse,
    KpiItem,
    EnergyFlowResponse,
    TimeSeriesPoint
)
from app.integration.ai_client import AIServiceClient, AIServiceError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class SimulationEngine:
    """
    Central simulation engine ensuring data consistency across all views:
    Overview, Forecasting, Battery Scheduling, Grid Optimization, and Analytics.
    """

    def __init__(self, seed: int = 42):
        self.pv_provider = MockPVForecastProvider(seed=seed)
        self.load_provider = MockLoadForecastProvider(seed=seed)
        self.battery_optimizer = MockBatteryOptimizationProvider()
        self.ai_client = AIServiceClient(
            base_url=settings.AI_SERVICE_URL,
            timeout=settings.AI_SERVICE_TIMEOUT_SECONDS,
            start_time=settings.AI_SIMULATION_START_TIME,
        )

    def get_effective_configs(self, db: Optional[Session] = None) -> tuple[BatteryConfigSchema, GridConfigSchema, dict]:
        """Load configuration from DB if available, else return defaults."""
        bat_cfg = None
        grid_cfg = None
        pv_cfg = {
            "installed_capacity_kw": 50.0,
            "derating_factor": 0.85,
            "system_efficiency": 0.90,
            "pv_model_identifier": "open-meteo-xgboost-v1"
        }

        if db:
            db_bat = db.query(BatteryConfiguration).filter(BatteryConfiguration.is_active == True).first()
            if db_bat:
                bat_cfg = BatteryConfigSchema.model_validate(db_bat)

            db_grid = db.query(GridConfiguration).filter(GridConfiguration.is_active == True).first()
            if db_grid:
                grid_cfg = GridConfigSchema.model_validate(db_grid)

            # Check for PV settings in system_settings
            pv_setting = db.query(SystemSetting).filter(SystemSetting.key == "pv_config").first()
            if pv_setting:
                import json
                try:
                    pv_cfg.update(json.loads(pv_setting.value))
                except Exception:
                    pass

        if not bat_cfg:
            bat_cfg = BatteryConfigSchema(
                capacity_kwh=100.0,
                initial_soc=50.0,
                min_soc=20.0,
                max_soc=95.0,
                max_charge_kw=30.0,
                max_discharge_kw=30.0,
                charge_efficiency=0.92,
                discharge_efficiency=0.92,
                battery_health=98.5
            )

        if not grid_cfg:
            grid_cfg = GridConfigSchema(
                import_limit_kw=150.0,
                export_limit_kw=100.0,
                import_tariff=0.15,
                export_tariff=0.08
            )

        return bat_cfg, grid_cfg, pv_cfg

    def get_simulation_state(self, db: Optional[Session] = None, reference_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Generate unified simulation state covering 24h forecast and schedule.
        """
        now = reference_time or datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        bat_cfg, grid_cfg, pv_cfg = self.get_effective_configs(db)

        try:
            ai_payload = self.ai_client.simulate(horizon_hours=24)
            ai_state = self.ai_client.to_dashboard_state(
                ai_payload, capacity_kwh=bat_cfg.capacity_kwh
            )
            return {
                **ai_state,
                "battery_config": bat_cfg,
                "grid_config": grid_cfg,
                "pv_config": pv_cfg,
                "reference_time": now,
            }
        except AIServiceError as exc:
            logger.warning("AI service unavailable; using labeled offline fallback: %s", exc)

        pv_forecast = self.pv_provider.forecast_pv(
            horizon_hours=24,
            start_time=now,
            model_id=pv_cfg.get("pv_model_identifier", "open-meteo-xgboost-v1"),
            installed_capacity_kw=pv_cfg.get("installed_capacity_kw", 50.0),
            derating_factor=pv_cfg.get("derating_factor", 0.85)
        )

        load_forecast = self.load_provider.forecast_load(
            horizon_hours=24,
            start_time=now,
            model_id="lstm-load-forecaster-v1"
        )

        schedule = self.battery_optimizer.generate_schedule(
            pv_forecast=pv_forecast,
            load_forecast=load_forecast,
            battery_config=bat_cfg,
            grid_config=grid_cfg,
            current_soc=bat_cfg.initial_soc,
            horizon_hours=24
        )

        return {
            "pv_forecast": pv_forecast,
            "load_forecast": load_forecast,
            "schedule": schedule,
            "battery_config": bat_cfg,
            "grid_config": grid_cfg,
            "pv_config": pv_cfg,
            "reference_time": now
        }

    def get_current_dashboard_data(self, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Compute current KPI metrics, dynamic energy flow routing, and 24h time-series chart data.
        """
        sim_state = self.get_simulation_state(db)
        schedule = sim_state["schedule"]
        bat_cfg = sim_state["battery_config"]
        grid_cfg = sim_state["grid_config"]

        # Step 0 represents current hour, step 1 is next hour
        current_step = schedule.steps[0] if schedule.steps else None
        next_step = schedule.steps[1] if len(schedule.steps) > 1 else current_step

        current_pv = current_step.pv_forecast_kw if current_step else 0.0
        current_load = current_step.load_forecast_kw if current_step else 0.0
        battery_power = current_step.battery_power_kw if current_step else 0.0
        if current_step and current_step.action == "DISCHARGE":
            battery_power = -battery_power  # negative for discharge
        battery_soc = current_step.soc_after if current_step else bat_cfg.initial_soc
        grid_import = current_step.grid_import_kw if current_step else 0.0
        grid_export = current_step.grid_export_kw if current_step else 0.0

        # Current hourly energy cost rate
        cost_rate = round(grid_import * grid_cfg.import_tariff - grid_export * grid_cfg.export_tariff, 2)

        # Renewable utilization % = (solar consumed directly or stored) / total solar produced (or load covered by solar)
        renewable_utilization = 100.0
        if current_load > 0:
            solar_supplied = min(current_pv, current_load)
            bat_supplied = max(0.0, -battery_power)
            renewable_utilization = min(100.0, round(((solar_supplied + bat_supplied) / current_load) * 100.0, 1))

        # Next hour forecast values
        next_pv = next_step.pv_forecast_kw if next_step else 0.0
        next_load = next_step.load_forecast_kw if next_step else 0.0

        # Flow breakdown for EnergyFlow diagram
        flow_pv_to_load = min(current_pv, current_load)
        excess_pv = max(0.0, current_pv - current_load)
        flow_pv_to_battery = current_step.battery_power_kw if (current_step and current_step.action == "CHARGE") else 0.0
        flow_pv_to_grid = max(0.0, excess_pv - flow_pv_to_battery)
        flow_battery_to_load = current_step.battery_power_kw if (current_step and current_step.action == "DISCHARGE") else 0.0
        flow_grid_to_load = grid_import

        # Operational status assessment
        operational_status = "Normal"
        status_msg = "Micro-grid operating stably within nominal dispatch envelope."
        if battery_soc <= bat_cfg.min_soc + 2.0:
            operational_status = "Warning"
            status_msg = "Battery SOC near minimum threshold (20%). Discharging limited."
        elif grid_import >= grid_cfg.import_limit_kw * 0.90:
            operational_status = "Critical"
            status_msg = f"Grid import ({grid_import:.1f} kW) approaching interconnection capacity ({grid_cfg.import_limit_kw:.1f} kW)."
        elif battery_soc >= bat_cfg.max_soc - 2.0:
            operational_status = "Normal"
            status_msg = "Battery fully charged. Surplus solar routed to grid export."

        # KPI objects
        kpis = OverviewKpisResponse(
            current_pv_kw=KpiItem(
                label="Current PV Generation",
                value=current_pv,
                unit="kW",
                status="success" if current_pv > 10 else "normal",
                change_pct=round(((current_pv - 15.0) / 15.0) * 100, 1) if current_pv > 0 else 0.0,
                change_period="vs 1h ago"
            ),
            current_load_kw=KpiItem(
                label="Current Load Demand",
                value=current_load,
                unit="kW",
                status="normal" if current_load < 45 else "warning",
                change_pct=3.2,
                change_period="vs 1h ago"
            ),
            battery_soc_pct=KpiItem(
                label="Battery SOC",
                value=battery_soc,
                unit="%",
                status="critical" if battery_soc < bat_cfg.min_soc + 2 else ("warning" if battery_soc < 30 else "success"),
                change_pct=round(battery_soc - current_step.soc_before, 1) if current_step else 0.0,
                change_period="this hour"
            ),
            grid_import_kw=KpiItem(
                label="Grid Import",
                value=grid_import,
                unit="kW",
                status="warning" if grid_import > 30 else "normal"
            ),
            grid_export_kw=KpiItem(
                label="Grid Export",
                value=grid_export,
                unit="kW",
                status="success" if grid_export > 5 else "normal"
            ),
            current_energy_cost=KpiItem(
                label="Current Energy Cost",
                value=cost_rate,
                unit="$/hr",
                status="normal" if cost_rate <= 3.0 else "warning"
            ),
            renewable_utilization_pct=KpiItem(
                label="Renewable Utilization",
                value=renewable_utilization,
                unit="%",
                status="success" if renewable_utilization >= 70 else "normal"
            ),
            forecasted_pv_next_hour_kw=KpiItem(
                label="Forecasted PV (+1h)",
                value=next_pv,
                unit="kW",
                status="normal"
            ),
            forecasted_load_next_hour_kw=KpiItem(
                label="Forecasted Load (+1h)",
                value=next_load,
                unit="kW",
                status="normal"
            )
        )

        status_label = (
            "LIVE MODEL OUTPUT"
            if not schedule.is_simulated
            else "OFFLINE FALLBACK / SIMULATED DATA"
        )
        energy_flow = EnergyFlowResponse(
            timestamp=current_step.timestamp if current_step else datetime.now(timezone.utc),
            pv_power_kw=current_pv,
            load_demand_kw=current_load,
            battery_power_kw=battery_power,
            battery_soc_pct=battery_soc,
            grid_import_kw=grid_import,
            grid_export_kw=grid_export,
            flow_pv_to_load_kw=round(flow_pv_to_load, 2),
            flow_pv_to_battery_kw=round(flow_pv_to_battery, 2),
            flow_pv_to_grid_kw=round(flow_pv_to_grid, 2),
            flow_battery_to_load_kw=round(flow_battery_to_load, 2),
            flow_grid_to_load_kw=round(flow_grid_to_load, 2),
            operational_status=operational_status,
            status_label=status_label
        )

        # 24h series for chart
        series: List[TimeSeriesPoint] = []
        for step in schedule.steps:
            b_pow = step.battery_power_kw if step.action == "CHARGE" else (-step.battery_power_kw if step.action == "DISCHARGE" else 0.0)
            series.append(
                TimeSeriesPoint(
                    timestamp=step.timestamp,
                    pv_generation_kw=step.pv_forecast_kw,
                    load_demand_kw=step.load_forecast_kw,
                    grid_import_kw=step.grid_import_kw,
                    grid_export_kw=step.grid_export_kw,
                    battery_soc_pct=step.soc_after,
                    battery_power_kw=b_pow
                )
            )

        return {
            "status_label": status_label,
            "operational_status": operational_status,
            "operational_status_message": status_msg,
            "kpis": kpis,
            "energy_flow": energy_flow,
            "series": series
        }


# Singleton engine instance
simulation_engine = SimulationEngine(seed=42)
