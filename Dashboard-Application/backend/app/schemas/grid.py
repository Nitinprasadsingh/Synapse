from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class GridConfigSchema(BaseModel):
    id: Optional[int] = None
    import_limit_kw: float = Field(..., ge=0, description="Max grid import limit (kW)")
    export_limit_kw: float = Field(..., ge=0, description="Max grid export limit (kW)")
    import_tariff: float = Field(..., ge=0, description="Cost per kWh imported ($/kWh)")
    export_tariff: float = Field(..., ge=0, description="Revenue per kWh exported ($/kWh)")
    is_active: bool = True
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GridConfigUpdate(BaseModel):
    import_limit_kw: Optional[float] = Field(None, ge=0)
    export_limit_kw: Optional[float] = Field(None, ge=0)
    import_tariff: Optional[float] = Field(None, ge=0)
    export_tariff: Optional[float] = Field(None, ge=0)


class GridStatusResponse(BaseModel):
    current_import_kw: float
    current_export_kw: float
    import_limit_kw: float
    export_limit_kw: float
    import_tariff: float
    export_tariff: float
    current_cost_rate_per_hour: float
    peak_grid_demand_kw: float
    renewable_utilization_pct: float
    status: str  # NORMAL, WARNING, CRITICAL
    status_label: str = "SIMULATED STATUS"


class HourlyGridPoint(BaseModel):
    timestamp: datetime
    grid_import_kw: float
    grid_export_kw: float
    import_cost: float
    export_revenue: float
    net_cost: float
    renewable_utilization_pct: float


class StrategyMetric(BaseModel):
    strategy_name: str
    total_grid_import_kwh: float
    total_grid_export_kwh: float
    total_cost: float
    peak_grid_demand_kw: float
    renewable_utilization_pct: float


class StrategyComparisonResponse(BaseModel):
    baseline_strategy: StrategyMetric
    scheduled_strategy: StrategyMetric
    cost_savings_amount: float
    cost_savings_pct: float
    import_reduction_kwh: float
    status_label: str = "SIMULATED STRATEGY COMPARISON"


class GridAnalyticsResponse(BaseModel):
    status_label: str = "SIMULATED DATA"
    total_import_kwh: float
    total_export_kwh: float
    total_import_cost: float
    total_export_revenue: float
    net_grid_cost: float
    peak_demand_kw: float
    average_renewable_utilization_pct: float
    hourly_series: List[HourlyGridPoint]
    strategy_comparison: StrategyComparisonResponse
