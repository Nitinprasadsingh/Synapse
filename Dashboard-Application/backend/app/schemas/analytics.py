from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class DailyEnergyItem(BaseModel):
    date: str
    pv_generation_kwh: float
    load_consumption_kwh: float
    battery_charge_kwh: float
    battery_discharge_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float
    net_cost: float
    renewable_utilization_pct: float
    peak_demand_kw: float


class BatteryCyclingStats(BaseModel):
    equivalent_full_cycles: float
    total_energy_throughput_kwh: float
    average_depth_of_discharge_pct: float
    estimated_soh_pct: float


class EnergyAnalyticsSummary(BaseModel):
    status_label: str = "SIMULATED DATA"
    period: str
    total_pv_kwh: float
    total_load_kwh: float
    total_battery_charge_kwh: float
    total_battery_discharge_kwh: float
    total_grid_import_kwh: float
    total_grid_export_kwh: float
    total_energy_cost: float
    renewable_utilization_pct: float
    peak_demand_kw: float
    battery_stats: BatteryCyclingStats
    daily_breakdown: List[DailyEnergyItem]


class ReportExportItem(BaseModel):
    report_type: str
    generated_at: datetime
    data: List[DailyEnergyItem]
