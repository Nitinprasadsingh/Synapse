from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime
from app.db.database import Base


class PVForecast(Base):
    __tablename__ = "pv_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    horizon_hours = Column(Integer, default=24, nullable=False)
    generation_kw = Column(Float, nullable=False)
    lower_bound_kw = Column(Float, nullable=True)
    upper_bound_kw = Column(Float, nullable=True)
    model_id = Column(String(100), default="open-meteo-xgboost-v1", nullable=False)
    is_simulated = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class LoadForecast(Base):
    __tablename__ = "load_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    horizon_hours = Column(Integer, default=24, nullable=False)
    demand_kw = Column(Float, nullable=False)
    expected_peak_kw = Column(Float, nullable=True)
    expected_min_kw = Column(Float, nullable=True)
    model_id = Column(String(100), default="lstm-load-forecaster-v1", nullable=False)
    is_simulated = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
