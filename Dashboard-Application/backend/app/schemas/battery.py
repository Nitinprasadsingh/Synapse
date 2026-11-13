from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BatteryConfigSchema(BaseModel):
    id: Optional[int] = None
    capacity_kwh: float = Field(..., gt=0, description="Total battery capacity in kWh")
    initial_soc: float = Field(..., ge=0, le=100, description="Initial State of Charge (%)")
    min_soc: float = Field(..., ge=0, le=100, description="Minimum allowable SOC (%)")
    max_soc: float = Field(..., ge=0, le=100, description="Maximum allowable SOC (%)")
    max_charge_kw: float = Field(..., ge=0, description="Maximum charging power (kW)")
    max_discharge_kw: float = Field(..., ge=0, description="Maximum discharging power (kW)")
    charge_efficiency: float = Field(..., gt=0, le=1.0, description="Charging efficiency [0.0 - 1.0]")
    discharge_efficiency: float = Field(..., gt=0, le=1.0, description="Discharging efficiency [0.0 - 1.0]")
    battery_health: float = Field(default=98.5, ge=0, le=100)
    is_active: bool = True
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BatteryConfigUpdate(BaseModel):
    capacity_kwh: Optional[float] = Field(None, gt=0)
    initial_soc: Optional[float] = Field(None, ge=0, le=100)
    min_soc: Optional[float] = Field(None, ge=0, le=100)
    max_soc: Optional[float] = Field(None, ge=0, le=100)
    max_charge_kw: Optional[float] = Field(None, ge=0)
    max_discharge_kw: Optional[float] = Field(None, ge=0)
    charge_efficiency: Optional[float] = Field(None, gt=0, le=1.0)
    discharge_efficiency: Optional[float] = Field(None, gt=0, le=1.0)
    battery_health: Optional[float] = Field(None, ge=0, le=100)


class BatteryStatusResponse(BaseModel):
    capacity_kwh: float
    current_soc: float
    min_soc: float
    max_soc: float
    max_charge_kw: float
    max_discharge_kw: float
    charge_efficiency: float
    discharge_efficiency: float
    battery_health: float
    current_power_kw: float  # + charging, - discharging
    mode: str  # CHARGING, DISCHARGING, IDLE
    operational_status: str  # NORMAL, WARNING, CRITICAL
    status_label: str = "OFFLINE FALLBACK / SIMULATED STATUS"


class BatteryScheduleStepSchema(BaseModel):
    step_index: int
    timestamp: datetime
    pv_forecast_kw: float
    load_forecast_kw: float
    action: str  # CHARGE, DISCHARGE, IDLE
    battery_power_kw: float
    soc_before: float
    soc_after: float
    grid_import_kw: float
    grid_export_kw: float
    step_cost: float

    model_config = ConfigDict(from_attributes=True)


class BatteryScheduleResponse(BaseModel):
    schedule_id: str
    generated_at: datetime
    status: str
    total_cost: float
    algorithm: str
    is_simulated: bool = True
    status_label: str = "OFFLINE FALLBACK / SIMULATED SCHEDULE"
    notes: Optional[str] = None
    steps: List[BatteryScheduleStepSchema]

    model_config = ConfigDict(from_attributes=True)


class BatteryScheduleGenerateRequest(BaseModel):
    horizon_hours: int = 24
    custom_initial_soc: Optional[float] = None
