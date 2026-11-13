import math
import random
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from app.forecasting.interfaces import PVForecastProvider, LoadForecastProvider
from app.schemas.forecast import (
    ForecastPoint,
    PVForecastResponse,
    LoadForecastResponse,
    LoadForecastSummary
)


class MockPVForecastProvider(PVForecastProvider):
    """
    Mock PV forecasting provider generating realistic bell-curve solar generation
    with atmospheric solar zenith modeling and cloud attenuation.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed

    def _calculate_pv(self, hour_of_day: float, installed_kw: float, derating: float, rng: random.Random) -> float:
        # Solar window roughly 06:00 to 18:30
        sunrise = 6.0
        sunset = 18.5
        if sunrise <= hour_of_day <= sunset:
            # Solar zenith angle approximation (half sine)
            t = (hour_of_day - sunrise) / (sunset - sunrise)
            solar_potential = math.sin(t * math.pi) ** 1.3
            # Add minor cloud variability (+/- 8%)
            noise = rng.uniform(0.92, 1.05)
            pv = installed_kw * derating * solar_potential * noise
            return round(max(0.0, pv), 2)
        return 0.0

    def forecast_pv(
        self,
        horizon_hours: int = 24,
        start_time: Optional[datetime] = None,
        model_id: str = "open-meteo-xgboost-v1",
        installed_capacity_kw: float = 50.0,
        derating_factor: float = 0.85
    ) -> PVForecastResponse:
        now = start_time or datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        rng = random.Random(self.seed + int(now.timestamp()) // 3600)

        # Historical 24h
        historical_points: List[ForecastPoint] = []
        for h in range(-24, 0):
            ts = now + timedelta(hours=h)
            val = self._calculate_pv(ts.hour, installed_capacity_kw, derating_factor, rng)
            historical_points.append(
                ForecastPoint(
                    timestamp=ts,
                    horizon_hour=h,
                    value_kw=val,
                    lower_bound_kw=round(max(0.0, val * 0.9), 2),
                    upper_bound_kw=round(val * 1.1, 2),
                    is_historical=True
                )
            )

        # Future forecast 24h
        forecast_points: List[ForecastPoint] = []
        for h in range(0, horizon_hours):
            ts = now + timedelta(hours=h)
            val = self._calculate_pv(ts.hour, installed_capacity_kw, derating_factor, rng)
            # Prediction interval expands further in future horizon
            uncertainty = 0.05 + (h / horizon_hours) * 0.12
            forecast_points.append(
                ForecastPoint(
                    timestamp=ts,
                    horizon_hour=h,
                    value_kw=val,
                    lower_bound_kw=round(max(0.0, val * (1 - uncertainty)), 2),
                    upper_bound_kw=round(val * (1 + uncertainty), 2),
                    is_historical=False
                )
            )

        model_name = "Open-Meteo Operational XGBoost" if "open-meteo" in model_id.lower() else "NSRDB Benchmark XGBoost"

        return PVForecastResponse(
            model_id=model_id,
            model_name=model_name,
            forecast_timestamp=now,
            horizon_hours=horizon_hours,
            is_simulated=True,
            unit="kW",
            status_label="SIMULATED DATA",
            forecast_points=forecast_points,
            historical_points=historical_points
        )


class MockLoadForecastProvider(LoadForecastProvider):
    """
    Mock Load forecasting provider generating realistic industrial/commercial
    load profile with morning ramp, daytime activity, and evening peak.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed

    def _calculate_load(self, hour_of_day: float, base_kw: float, rng: random.Random) -> float:
        # Base load at night ~ 15-20 kW
        # Morning peak ~ 08:00 - 11:00 (35-45 kW)
        # Afternoon sustained ~ 30-38 kW
        # Evening peak ~ 18:00 - 21:00 (40-52 kW)
        h = hour_of_day
        if 0 <= h < 6:
            profile = 0.35 + 0.05 * math.sin((h / 6.0) * math.pi)
        elif 6 <= h < 12:
            profile = 0.40 + 0.50 * math.sin(((h - 6) / 6.0) * math.pi)
        elif 12 <= h < 17:
            profile = 0.70 + 0.10 * math.sin(((h - 12) / 5.0) * math.pi)
        elif 17 <= h < 22:
            profile = 0.75 + 0.25 * math.sin(((h - 17) / 5.0) * math.pi)
        else:
            profile = 0.55 - 0.20 * ((h - 22) / 2.0)

        noise = rng.uniform(0.95, 1.05)
        load = base_kw * profile * noise
        return round(max(5.0, load), 2)

    def forecast_load(
        self,
        horizon_hours: int = 24,
        start_time: Optional[datetime] = None,
        model_id: str = "lstm-load-forecaster-v1"
    ) -> LoadForecastResponse:
        now = start_time or datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        rng = random.Random(self.seed + 100 + int(now.timestamp()) // 3600)
        nominal_peak_capacity = 55.0

        # Historical 24h
        historical_points: List[ForecastPoint] = []
        for h in range(-24, 0):
            ts = now + timedelta(hours=h)
            val = self._calculate_load(ts.hour, nominal_peak_capacity, rng)
            historical_points.append(
                ForecastPoint(
                    timestamp=ts,
                    horizon_hour=h,
                    value_kw=val,
                    lower_bound_kw=round(val * 0.92, 2),
                    upper_bound_kw=round(val * 1.08, 2),
                    is_historical=True
                )
            )

        # Future forecast
        forecast_points: List[ForecastPoint] = []
        vals: List[float] = []
        for h in range(0, horizon_hours):
            ts = now + timedelta(hours=h)
            val = self._calculate_load(ts.hour, nominal_peak_capacity, rng)
            vals.append(val)
            uncertainty = 0.04 + (h / horizon_hours) * 0.08
            forecast_points.append(
                ForecastPoint(
                    timestamp=ts,
                    horizon_hour=h,
                    value_kw=val,
                    lower_bound_kw=round(val * (1 - uncertainty), 2),
                    upper_bound_kw=round(val * (1 + uncertainty), 2),
                    is_historical=False
                )
            )

        peak_demand = max(vals)
        min_demand = min(vals)
        avg_demand = round(sum(vals) / len(vals), 2)
        total_energy = round(sum(vals), 2)

        return LoadForecastResponse(
            model_id=model_id,
            model_name="Recurrent LSTM Load Forecaster (Operational)",
            forecast_timestamp=now,
            horizon_hours=horizon_hours,
            is_simulated=True,
            unit="kW",
            status_label="SIMULATED DATA",
            summary=LoadForecastSummary(
                expected_peak_kw=round(peak_demand, 2),
                expected_min_kw=round(min_demand, 2),
                average_demand_kw=avg_demand,
                total_energy_kwh=total_energy
            ),
            forecast_points=forecast_points,
            historical_points=historical_points
        )
