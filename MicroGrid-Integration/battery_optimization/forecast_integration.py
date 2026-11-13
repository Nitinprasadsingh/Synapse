"""Adapters for the trained PV and county-load forecasting artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from battery_optimization.config import MicrogridConfig
from battery_optimization.exceptions import ForecastError


class ForecastIntegrationService:
    """Generate reproducible operational forecasts from the saved model artifacts.

    The default mode is historical replay: it uses the weather and load rows
    shipped with the project, which makes offline tests deterministic. Live
    weather acquisition can be added by supplying a DataFrame with the same
    Open-Meteo feature columns to :meth:`generate_pv_forecast`.
    """

    def __init__(
        self,
        config: MicrogridConfig,
        project_root: Optional[str | Path] = None,
    ) -> None:
        self.config = config
        root = Path(project_root) if project_root else Path(__file__).resolve().parent.parent
        self.root = root
        self.pv_dir = root / "notebooks" / "open-meteo-model_artifacts"
        self.load_dir = root / "notebooks" / "load_forecasting_artifacts"
        try:
            self.pv_features = json.loads(
                (self.pv_dir / "pv_model_features.json").read_text(encoding="utf-8")
            )
            self.load_features = json.loads(
                (self.load_dir / "load_model_features.json").read_text(encoding="utf-8")
            )["features"]
            self.pv_model = XGBRegressor()
            self.pv_model.load_model(str(self.pv_dir / "deployment_pv_xgboost_model.json"))
            self.load_model = XGBRegressor()
            self.load_model.load_model(str(self.load_dir / "load_xgboost_model.json"))
            self.pv_data = pd.read_csv(self.pv_dir / "prepared_pv_forecasting_dataset.csv")
            self.load_data = pd.read_csv(
                self.load_dir / "load_clean_2017_2019.csv",
                parse_dates=["Timestamp_UTC", "Local_Time"],
            )
        except (OSError, ValueError, KeyError) as exc:
            raise ForecastError(f"Unable to load forecast artifacts: {exc}") from exc

        self.pv_data["time"] = pd.to_datetime(self.pv_data["time"], utc=True)
        self.load_data["Timestamp_UTC"] = pd.to_datetime(
            self.load_data["Timestamp_UTC"], utc=True
        )
        self.load_data = self.load_data.sort_values("Timestamp_UTC").set_index("Timestamp_UTC")

    def _timestamps(self, start_time: pd.Timestamp, horizon_hours: int) -> pd.DatetimeIndex:
        if horizon_hours <= 0:
            raise ForecastError("horizon_hours must be positive")
        start = pd.Timestamp(start_time)
        if start.tzinfo is None:
            start = start.tz_localize("UTC")
        # ``start`` is normalized to UTC above; passing a second ``tz`` value
        # makes newer pandas versions reject the already tz-aware endpoint.
        return pd.date_range(start, periods=horizon_hours, freq="h")

    def generate_pv_forecast(
        self,
        start_time: pd.Timestamp,
        horizon_hours: int,
        weather: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        timestamps = self._timestamps(start_time, horizon_hours)
        if weather is None:
            data = self.pv_data[self.pv_data["time"].isin(timestamps)].copy()
            if len(data) != horizon_hours:
                missing = sorted(set(timestamps) - set(data["time"]))
                raise ForecastError(f"PV forecast data is missing timestamps: {missing[:5]}")
        else:
            data = weather.copy()
            if "time" not in data:
                raise ForecastError("weather must contain a 'time' column")
            data["time"] = pd.to_datetime(data["time"], utc=True)
            data = data[data["time"].isin(timestamps)].copy()
            if len(data) != horizon_hours:
                raise ForecastError("weather does not contain a complete hourly horizon")

        features = self.pv_features
        missing_columns = [c for c in features if c not in data.columns]
        if missing_columns:
            raise ForecastError(f"PV input is missing model features: {missing_columns}")
        frame = data.sort_values("time").copy()
        dt = frame["time"].dt.tz_convert(self.config.timezone)
        frame["hour_sin"] = np.sin(2 * np.pi * dt.dt.hour / 24.0)
        frame["hour_cos"] = np.cos(2 * np.pi * dt.dt.hour / 24.0)
        frame["month"] = dt.dt.month
        frame["dayofweek"] = dt.dt.dayofweek
        predictions = np.maximum(0.0, self.pv_model.predict(frame[features]))
        predictions = np.minimum(predictions, self.config.pv_capacity_kw)
        return pd.DataFrame(
            {"Timestamp": frame["time"].to_numpy(), "PV_Forecast_kW": predictions}
        )

    def generate_load_forecast(
        self,
        start_time: pd.Timestamp,
        horizon_hours: int,
    ) -> pd.DataFrame:
        timestamps = self._timestamps(start_time, horizon_hours)
        history = self.load_data.copy()
        if timestamps.min() <= history.index.min() + pd.Timedelta(hours=168):
            raise ForecastError("Load forecasting requires at least 168 hours of prior history")
        required = pd.date_range(
            timestamps.min() - pd.Timedelta(hours=168),
            timestamps.max(),
            freq="h",
        )
        history = history.reindex(required)
        if history["Load_MW"].isna().any():
            raise ForecastError("Load history has gaps required for lag features")

        frame = pd.DataFrame(index=required)
        frame["Load_MW"] = history["Load_MW"]
        local = frame.index.tz_convert(self.config.timezone)
        frame["Hour"] = local.hour
        frame["DayOfWeek"] = local.dayofweek
        frame["DayOfMonth"] = local.day
        frame["Month"] = local.month
        frame["DayOfYear"] = local.dayofyear
        frame["IsWeekend"] = (local.dayofweek >= 5).astype(int)
        frame["Hour_sin"] = np.sin(2 * np.pi * frame["Hour"] / 24.0)
        frame["Hour_cos"] = np.cos(2 * np.pi * frame["Hour"] / 24.0)
        frame["DayOfWeek_sin"] = np.sin(2 * np.pi * frame["DayOfWeek"] / 7.0)
        frame["DayOfWeek_cos"] = np.cos(2 * np.pi * frame["DayOfWeek"] / 7.0)
        frame["Month_sin"] = np.sin(2 * np.pi * frame["Month"] / 12.0)
        frame["Month_cos"] = np.cos(2 * np.pi * frame["Month"] / 12.0)
        for lag in (1, 2, 3, 6, 12, 24, 48, 168):
            frame[f"Load_lag_{lag}"] = frame["Load_MW"].shift(lag)
        for window in (3, 6, 24, 168):
            frame[f"RollingMean_{window}"] = frame["Load_MW"].shift(1).rolling(window).mean()
        for window in (24, 168):
            frame[f"RollingStd_{window}"] = frame["Load_MW"].shift(1).rolling(window).std()
        prediction_rows = frame.loc[timestamps]
        predictions_mw = self.load_model.predict(prediction_rows[self.load_features])
        predictions_kw = [
            self.config.scaling.scale_mw_to_kw(float(value)) for value in predictions_mw
        ]
        return pd.DataFrame({"Timestamp": timestamps, "Load_Forecast_kW": predictions_kw})

    def integrate_forecasts(
        self, pv_forecast: pd.DataFrame, load_forecast: pd.DataFrame
    ) -> pd.DataFrame:
        required_pv = {"Timestamp", "PV_Forecast_kW"}
        required_load = {"Timestamp", "Load_Forecast_kW"}
        if not required_pv.issubset(pv_forecast) or not required_load.issubset(load_forecast):
            raise ForecastError("Forecast frames have incompatible columns")
        result = pd.merge(
            pv_forecast[list(required_pv)],
            load_forecast[list(required_load)],
            on="Timestamp",
            how="outer",
            validate="one_to_one",
        ).sort_values("Timestamp")
        if result[["PV_Forecast_kW", "Load_Forecast_kW"]].isna().any().any():
            raise ForecastError("PV and load forecasts do not have aligned timestamps")
        if len(result) > 1 and not (result["Timestamp"].diff().dropna() == pd.Timedelta(hours=1)).all():
            raise ForecastError("Integrated forecasts are not hourly and continuous")
        result["Load_Forecast_Source"] = "SIMULATED_COUNTY_SCALED"
        result["PV_Forecast_Source"] = "OPEN_METEO_XGBOOST"
        return result.reset_index(drop=True)

    def get_forecast(self, start_time: pd.Timestamp, horizon_hours: int) -> dict:
        integrated = self.integrate_forecasts(
            self.generate_pv_forecast(start_time, horizon_hours),
            self.generate_load_forecast(start_time, horizon_hours),
        )
        return {
            "timestamps": integrated["Timestamp"].tolist(),
            "pv_kw": integrated["PV_Forecast_kW"].astype(float).tolist(),
            "load_kw": integrated["Load_Forecast_kW"].astype(float).tolist(),
        }
