from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class KpiItem(BaseModel):
    label: str
    value: float
    unit: str
    status: str = "normal"  # normal, warning, critical, success
    change_pct: Optional[float] = None
    change_period: Optional[str] = None


class OverviewKpisResponse(BaseModel):
    current_pv_kw: KpiItem
    current_load_kw: KpiItem
    battery_soc_pct: KpiItem
    grid_import_kw: KpiItem
    grid_export_kw: KpiItem
    current_energy_cost: KpiItem
    renewable_utilization_pct: KpiItem
    forecasted_pv_next_hour_kw: KpiItem
    forecasted_load_next_hour_kw: KpiItem


class EnergyFlowResponse(BaseModel):
    timestamp: datetime
    pv_power_kw: float
    load_demand_kw: float
    battery_power_kw: float  # + charging, - discharging
    battery_soc_pct: float
    grid_import_kw: float
    grid_export_kw: float
    flow_pv_to_load_kw: float
    flow_pv_to_battery_kw: float
    flow_pv_to_grid_kw: float
    flow_battery_to_load_kw: float
    flow_grid_to_load_kw: float
    operational_status: str  # NORMAL, WARNING, CRITICAL
    status_label: str = "OFFLINE FALLBACK / SIMULATED DATA"


class TimeSeriesPoint(BaseModel):
    timestamp: datetime
    pv_generation_kw: float
    load_demand_kw: float
    grid_import_kw: float
    grid_export_kw: float
    battery_soc_pct: float
    battery_power_kw: float


class OverviewDashboardResponse(BaseModel):
    status_label: str = "OFFLINE FALLBACK / SIMULATED DATA"
    operational_status: str  # Normal, Warning, Critical
    operational_status_message: str
    kpis: OverviewKpisResponse
    energy_flow: EnergyFlowResponse
    series: List[TimeSeriesPoint]
