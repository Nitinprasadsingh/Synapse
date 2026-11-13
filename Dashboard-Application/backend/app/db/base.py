# Import all the models, so that Base has them before being
# imported by Alembic or database initialization
from app.db.database import Base
from app.models.user import User
from app.models.forecast import PVForecast, LoadForecast
from app.models.battery import BatteryConfiguration, BatterySchedule, BatteryScheduleStep
from app.models.grid import GridConfiguration
from app.models.alert import SystemAlert
from app.models.measurement import EnergyMeasurement, EnergyReport
from app.models.settings import SystemSetting
from app.models.model_metadata import ModelMetadata
