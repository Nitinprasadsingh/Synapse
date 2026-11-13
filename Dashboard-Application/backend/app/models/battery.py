from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base


class BatteryConfiguration(Base):
    __tablename__ = "battery_configurations"

    id = Column(Integer, primary_key=True, index=True)
    capacity_kwh = Column(Float, default=100.0, nullable=False)
    initial_soc = Column(Float, default=50.0, nullable=False)
    min_soc = Column(Float, default=20.0, nullable=False)
    max_soc = Column(Float, default=95.0, nullable=False)
    max_charge_kw = Column(Float, default=30.0, nullable=False)
    max_discharge_kw = Column(Float, default=30.0, nullable=False)
    charge_efficiency = Column(Float, default=0.92, nullable=False)
    discharge_efficiency = Column(Float, default=0.92, nullable=False)
    battery_health = Column(Float, default=98.5, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class BatterySchedule(Base):
    __tablename__ = "battery_schedules"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(String(100), unique=True, index=True, nullable=False)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(String(50), default="GENERATED", nullable=False)
    total_cost = Column(Float, default=0.0, nullable=False)
    algorithm = Column(String(100), default="Heuristic-Rule-Engine (SIMULATED)", nullable=False)
    is_simulated = Column(Boolean, default=True, nullable=False)
    notes = Column(String(255), nullable=True)

    steps = relationship("BatteryScheduleStep", back_populates="schedule", cascade="all, delete-orphan")


class BatteryScheduleStep(Base):
    __tablename__ = "battery_schedule_steps"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("battery_schedules.id"), nullable=False, index=True)
    step_index = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    pv_forecast_kw = Column(Float, nullable=False)
    load_forecast_kw = Column(Float, nullable=False)
    action = Column(String(20), nullable=False)  # CHARGE, DISCHARGE, IDLE
    battery_power_kw = Column(Float, nullable=False)
    soc_before = Column(Float, nullable=False)
    soc_after = Column(Float, nullable=False)
    grid_import_kw = Column(Float, default=0.0, nullable=False)
    grid_export_kw = Column(Float, default=0.0, nullable=False)
    step_cost = Column(Float, default=0.0, nullable=False)

    schedule = relationship("BatterySchedule", back_populates="steps")
