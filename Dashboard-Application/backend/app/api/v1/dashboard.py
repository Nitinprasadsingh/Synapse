from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_analyst
from app.models.user import User
from app.simulation.mock_engine import simulation_engine
from app.schemas.dashboard import (
    OverviewDashboardResponse,
    EnergyFlowResponse,
    OverviewKpisResponse
)

router = APIRouter()


@router.get("/overview", response_model=OverviewDashboardResponse)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Get consolidated dashboard metrics, operational state, energy flow, and 24h time-series.
    """
    data = simulation_engine.get_current_dashboard_data(db)
    return data


@router.get("/energy-flow", response_model=EnergyFlowResponse)
def get_energy_flow(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Get instantaneous micro-grid power flow routing:
    PV -> Load / Battery / Grid, Battery -> Load, Grid -> Load.
    """
    data = simulation_engine.get_current_dashboard_data(db)
    return data["energy_flow"]


@router.get("/kpis", response_model=OverviewKpisResponse)
def get_kpis(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Retrieve key operational performance indicators (PV, Load, SOC, Grid import/export, cost, renewable %).
    """
    data = simulation_engine.get_current_dashboard_data(db)
    return data["kpis"]
