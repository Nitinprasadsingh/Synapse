from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from app.schemas.forecast import PVForecastResponse, LoadForecastResponse


class PVForecastProvider(ABC):
    """
    Abstract interface for Solar PV Generation Forecasting Providers.
    Operational implementations (e.g. Open-Meteo XGBoost, NSRDB Benchmark)
    must implement this interface.
    """

    @abstractmethod
    def forecast_pv(
        self,
        horizon_hours: int = 24,
        start_time: Optional[datetime] = None,
        model_id: str = "open-meteo-xgboost-v1",
        installed_capacity_kw: float = 50.0,
        derating_factor: float = 0.85
    ) -> PVForecastResponse:
        """
        Generate solar PV forecast for the specified horizon and timestamp.
        """
        pass


class LoadForecastProvider(ABC):
    """
    Abstract interface for Electricity Load Demand Forecasting Providers.
    Operational implementations (e.g. LSTM / XGBoost Load Forecaster)
    must implement this interface.
    """

    @abstractmethod
    def forecast_load(
        self,
        horizon_hours: int = 24,
        start_time: Optional[datetime] = None,
        model_id: str = "lstm-load-forecaster-v1"
    ) -> LoadForecastResponse:
        """
        Generate electricity load demand forecast for the specified horizon and timestamp.
        """
        pass
