from typing import Optional
from pydantic import BaseModel, Field, model_validator


class PVSettings(BaseModel):
    installed_capacity_kw: float = Field(..., gt=0, description="Installed PV capacity in kW")
    derating_factor: float = Field(0.85, gt=0, le=1.0, description="PV derating factor (0-1)")
    system_efficiency: float = Field(0.90, gt=0, le=1.0, description="Inverter/system efficiency (0-1)")
    pv_model_identifier: str = Field("open-meteo-xgboost-v1", description="Active PV model")


class BatterySettings(BaseModel):
    capacity_kwh: float = Field(..., gt=0)
    initial_soc: float = Field(50.0, ge=0, le=100)
    min_soc: float = Field(20.0, ge=0, le=100)
    max_soc: float = Field(95.0, ge=0, le=100)
    max_charge_kw: float = Field(30.0, ge=0)
    max_discharge_kw: float = Field(30.0, ge=0)
    charge_efficiency: float = Field(0.92, gt=0, le=1.0)
    discharge_efficiency: float = Field(0.92, gt=0, le=1.0)

    @model_validator(mode="after")
    def validate_soc_bounds(self):
        if self.min_soc > self.max_soc:
            raise ValueError("Minimum SOC cannot be greater than Maximum SOC")
        return self


class GridSettings(BaseModel):
    import_limit_kw: float = Field(..., ge=0)
    export_limit_kw: float = Field(..., ge=0)
    import_tariff: float = Field(0.15, ge=0)
    export_tariff: float = Field(0.08, ge=0)


class ForecastSettings(BaseModel):
    forecast_horizon_hours: int = Field(24, ge=1, le=168)
    scheduling_horizon_hours: int = Field(24, ge=1, le=168)
    optimization_interval_minutes: int = Field(60, ge=5, le=1440)
    forecast_update_interval_minutes: int = Field(60, ge=5, le=1440)


class AllSettingsResponse(BaseModel):
    pv: PVSettings
    battery: BatterySettings
    grid: GridSettings
    forecast: ForecastSettings


class SystemSettingsUpdate(BaseModel):
    pv: Optional[PVSettings] = None
    battery: Optional[BatterySettings] = None
    grid: Optional[GridSettings] = None
    forecast: Optional[ForecastSettings] = None
