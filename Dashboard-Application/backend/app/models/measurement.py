from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime
from app.db.database import Base


class EnergyMeasurement(Base):
    __tablename__ = "energy_measurements"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    pv_generation_kw = Column(Float, nullable=False)
    load_demand_kw = Column(Float, nullable=False)
    battery_soc = Column(Float, nullable=False)
    battery_power_kw = Column(Float, nullable=False)  # positive = charging, negative = discharging
    grid_import_kw = Column(Float, default=0.0, nullable=False)
    grid_export_kw = Column(Float, default=0.0, nullable=False)
    energy_cost = Column(Float, default=0.0, nullable=False)
    is_simulated = Column(Boolean, default=True, nullable=False)


class EnergyReport(Base):
    __tablename__ = "energy_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50), nullable=False)  # daily, weekly, monthly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    total_pv_kwh = Column(Float, nullable=False)
    total_load_kwh = Column(Float, nullable=False)
    total_battery_charge_kwh = Column(Float, nullable=False)
    total_battery_discharge_kwh = Column(Float, nullable=False)
    total_grid_import_kwh = Column(Float, nullable=False)
    total_grid_export_kwh = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    renewable_utilization_pct = Column(Float, nullable=False)
    peak_grid_kw = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
