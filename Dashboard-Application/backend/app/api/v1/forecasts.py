from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_analyst
from app.models.user import User
from app.models.model_metadata import ModelMetadata
from app.simulation.mock_engine import simulation_engine
from app.schemas.forecast import (
    PVForecastResponse,
    LoadForecastResponse,
    CombinedForecastResponse,
    CombinedForecastPoint,
    ModelMetadataSchema
)

router = APIRouter()


@router.get("/pv", response_model=PVForecastResponse)
def get_pv_forecast(
    horizon: int = Query(24, ge=1, le=168),
    model_id: Optional[str] = Query("open-meteo-xgboost-v1"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Get solar PV generation forecast for the next horizon hours.
    Distinguishes historical generation from future forecasted generation.
    """
    sim_state = simulation_engine.get_simulation_state(db)
    pv_resp = sim_state["pv_forecast"]
    return pv_resp


@router.get("/load", response_model=LoadForecastResponse)
def get_load_forecast(
    horizon: int = Query(24, ge=1, le=168),
    model_id: Optional[str] = Query("lstm-load-forecaster-v1"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Get 24-hour electricity demand forecast with peak, min, and average summary.
    """
    sim_state = simulation_engine.get_simulation_state(db)
    load_resp = sim_state["load_forecast"]
    return load_resp


@router.get("/combined", response_model=CombinedForecastResponse)
def get_combined_forecast(
    horizon: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Get synchronized PV vs Load forecast with Net Energy Surplus/Deficit.
    Net Power = PV Forecast - Load Forecast
    """
    sim_state = simulation_engine.get_simulation_state(db)
    pv_forecast = sim_state["pv_forecast"]
    load_forecast = sim_state["load_forecast"]

    points: List[CombinedForecastPoint] = []
    total_pv = 0.0
    total_load = 0.0
    surplus_hours = 0
    deficit_hours = 0

    num_pts = min(horizon, len(pv_forecast.forecast_points), len(load_forecast.forecast_points))
    for i in range(num_pts):
        pv_pt = pv_forecast.forecast_points[i]
        load_pt = load_forecast.forecast_points[i]

        pv_kw = pv_pt.value_kw
        load_kw = load_pt.value_kw
        net_kw = round(pv_kw - load_kw, 2)

        total_pv += pv_kw
        total_load += load_kw

        if net_kw >= 0:
            surplus_hours += 1
            state = "SURPLUS"
        else:
            deficit_hours += 1
            state = "DEFICIT"

        points.append(
            CombinedForecastPoint(
                timestamp=pv_pt.timestamp,
                hour=i,
                pv_kw=pv_kw,
                load_kw=load_kw,
                net_power_kw=net_kw,
                surplus_deficit_state=state
            )
        )

    return CombinedForecastResponse(
        forecast_timestamp=pv_forecast.forecast_timestamp,
        horizon_hours=num_pts,
        total_pv_kwh=round(total_pv, 2),
        total_load_kwh=round(total_load, 2),
        net_energy_kwh=round(total_pv - total_load, 2),
        surplus_hours=surplus_hours,
        deficit_hours=deficit_hours,
        status_label="SIMULATED DATA",
        points=points
    )


@router.get("/models", response_model=List[ModelMetadataSchema])
def get_model_metadata(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Retrieve registered model metadata (NSRDB Benchmark, Open-Meteo Operational, LSTM Load).
    """
    models = db.query(ModelMetadata).all()
    return models
