from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, Boolean, DateTime
from app.db.database import Base


class GridConfiguration(Base):
    __tablename__ = "grid_configurations"

    id = Column(Integer, primary_key=True, index=True)
    import_limit_kw = Column(Float, default=150.0, nullable=False)
    export_limit_kw = Column(Float, default=100.0, nullable=False)
    import_tariff = Column(Float, default=0.15, nullable=False)  # $/kWh or currency/kWh
    export_tariff = Column(Float, default=0.08, nullable=False)  # $/kWh
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
