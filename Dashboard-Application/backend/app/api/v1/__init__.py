from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.forecasts import router as forecasts_router
from app.api.v1.battery import router as battery_router
from app.api.v1.grid import router as grid_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.settings import router as settings_router
from app.api.v1.system import router as system_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(forecasts_router, prefix="/forecasts", tags=["Forecasting"])
api_router.include_router(battery_router, prefix="/battery", tags=["Battery Management"])
api_router.include_router(grid_router, prefix="/grid", tags=["Grid Optimization"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics & Reports"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["System Alerts"])
api_router.include_router(settings_router, prefix="/settings", tags=["System Settings"])
api_router.include_router(system_router, prefix="/system", tags=["System Operations"])
