from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.deps import get_db
from app.core.config import settings

router = APIRouter()
START_TIME = datetime.now(timezone.utc)


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Service health check verifying application and database connectivity.
    """
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "app_name": settings.PROJECT_NAME,
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }


@router.get("/status")
def system_status():
    """
    System operational metadata, demo mode status, and uptime.
    """
    uptime_seconds = int((datetime.now(timezone.utc) - START_TIME).total_seconds())
    return {
        "demo_mode": settings.DEMO_MODE,
        "simulation_refresh_seconds": settings.SIMULATION_REFRESH_SECONDS,
        "uptime_seconds": uptime_seconds,
        "default_models": {
            "pv_operational": "open-meteo-xgboost-v1",
            "pv_benchmark": "nsrdb-xgboost-benchmark",
            "load_forecaster": "lstm-load-forecaster-v1",
            "battery_optimizer": "heuristic-rule-engine-v1 (SIMULATED)"
        },
        "badge": "DEMO / SIMULATED DATA"
    }
