from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from app.db.database import Base


class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(100), unique=True, index=True, nullable=False)
    model_name = Column(String(200), nullable=False)
    model_type = Column(String(50), nullable=False)  # pv_forecast, load_forecast, battery_opt
    version = Column(String(50), default="1.0.0", nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="SIMULATED", nullable=False)  # OPERATIONAL, BENCHMARK, SIMULATED
    source = Column(String(100), nullable=True)  # NSRDB, Open-Meteo, Heuristic
    metrics_json = Column(Text, nullable=True)  # JSON string of metrics
    is_simulated = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
