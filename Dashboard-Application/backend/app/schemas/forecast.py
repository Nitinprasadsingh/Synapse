from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ForecastPoint(BaseModel):
    timestamp: datetime
    horizon_hour: int
    value_kw: float
    lower_bound_kw: Optional[float] = None
    upper_bound_kw: Optional[float] = None
    is_historical: bool = False


class PVForecastResponse(BaseModel):
    model_id: str
    model_name: str
    forecast_timestamp: datetime
    horizon_hours: int
    is_simulated: bool = True
    unit: str = "kW"
    status_label: str = "SIMULATED DATA"
    forecast_points: List[ForecastPoint]
    historical_points: List[ForecastPoint] = Field(default_factory=list)


class LoadForecastSummary(BaseModel):
    expected_peak_kw: float
    expected_min_kw: float
    average_demand_kw: float
    total_energy_kwh: float


class LoadForecastResponse(BaseModel):
    model_id: str
    model_name: str
    forecast_timestamp: datetime
    horizon_hours: int
    is_simulated: bool = True
    unit: str = "kW"
    status_label: str = "SIMULATED DATA"
    summary: LoadForecastSummary
    forecast_points: List[ForecastPoint]
    historical_points: List[ForecastPoint] = Field(default_factory=list)


class CombinedForecastPoint(BaseModel):
    timestamp: datetime
    hour: int
    pv_kw: float
    load_kw: float
    net_power_kw: float  # pv_kw - load_kw
    surplus_deficit_state: str  # SURPLUS or DEFICIT


class CombinedForecastResponse(BaseModel):
    forecast_timestamp: datetime
    horizon_hours: int
    total_pv_kwh: float
    total_load_kwh: float
    net_energy_kwh: float
    surplus_hours: int
    deficit_hours: int
    status_label: str = "SIMULATED DATA"
    points: List[CombinedForecastPoint]


class ModelMetadataSchema(BaseModel):
    model_id: str
    model_name: str
    model_type: str
    version: str
    description: Optional[str] = None
    status: str
    source: Optional[str] = None
    metrics_json: Optional[str] = None
    is_simulated: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
