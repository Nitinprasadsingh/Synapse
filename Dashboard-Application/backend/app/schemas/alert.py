from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SystemAlertSchema(BaseModel):
    id: int
    title: str
    message: str
    category: str  # Battery, PV, Load, Grid, System
    severity: str  # INFO, WARNING, CRITICAL
    is_acknowledged: bool
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class SystemAlertCreate(BaseModel):
    title: str
    message: str
    category: str
    severity: str


class SystemAlertAcknowledge(BaseModel):
    acknowledged_by: Optional[str] = "operator"
