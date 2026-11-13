from abc import ABC, abstractmethod
from typing import Optional
from app.schemas.forecast import PVForecastResponse, LoadForecastResponse
from app.schemas.battery import BatteryConfigSchema, BatteryScheduleResponse
from app.schemas.grid import GridConfigSchema


class BatteryOptimizationProvider(ABC):
    """
    Abstract interface for Battery Scheduling and Micro-Grid Optimization Providers.
    The future Python + OR-Tools / MPC optimization engine will implement this interface.
    """

    @abstractmethod
    def generate_schedule(
        self,
        pv_forecast: PVForecastResponse,
        load_forecast: LoadForecastResponse,
        battery_config: BatteryConfigSchema,
        grid_config: GridConfigSchema,
        current_soc: Optional[float] = None,
        horizon_hours: int = 24
    ) -> BatteryScheduleResponse:
        """
        Generate 24-hour battery charge/discharge schedule and grid import/export profile.
        """
        pass
