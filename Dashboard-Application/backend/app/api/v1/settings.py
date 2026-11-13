import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin, require_analyst
from app.models.user import User
from app.models.battery import BatteryConfiguration
from app.models.grid import GridConfiguration
from app.models.settings import SystemSetting
from app.simulation.mock_engine import simulation_engine
from app.schemas.settings import (
    AllSettingsResponse,
    SystemSettingsUpdate,
    PVSettings,
    BatterySettings,
    GridSettings,
    ForecastSettings
)

router = APIRouter()


@router.get("", response_model=AllSettingsResponse)
def get_all_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Retrieve all system configurations: PV, Battery, Grid, and Forecast.
    """
    bat_cfg, grid_cfg, pv_raw = simulation_engine.get_effective_configs(db)

    # Load forecast config from system_settings
    fc_setting = db.query(SystemSetting).filter(SystemSetting.key == "forecast_config").first()
    fc_raw = {
        "forecast_horizon_hours": 24,
        "scheduling_horizon_hours": 24,
        "optimization_interval_minutes": 60,
        "forecast_update_interval_minutes": 60
    }
    if fc_setting:
        try:
            fc_raw.update(json.loads(fc_setting.value))
        except Exception:
            pass

    return AllSettingsResponse(
        pv=PVSettings(**pv_raw),
        battery=BatterySettings(
            capacity_kwh=bat_cfg.capacity_kwh,
            initial_soc=bat_cfg.initial_soc,
            min_soc=bat_cfg.min_soc,
            max_soc=bat_cfg.max_soc,
            max_charge_kw=bat_cfg.max_charge_kw,
            max_discharge_kw=bat_cfg.max_discharge_kw,
            charge_efficiency=bat_cfg.charge_efficiency,
            discharge_efficiency=bat_cfg.discharge_efficiency
        ),
        grid=GridSettings(
            import_limit_kw=grid_cfg.import_limit_kw,
            export_limit_kw=grid_cfg.export_limit_kw,
            import_tariff=grid_cfg.import_tariff,
            export_tariff=grid_cfg.export_tariff
        ),
        forecast=ForecastSettings(**fc_raw)
    )


@router.put("", response_model=AllSettingsResponse)
def update_settings(
    update_data: SystemSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update system configurations. Requires ADMIN role. Validates constraints and updates DB.
    """
    now = datetime.now(timezone.utc)

    # 1. Update Battery
    if update_data.battery:
        db_bat = db.query(BatteryConfiguration).filter(BatteryConfiguration.is_active == True).first()
        if not db_bat:
            db_bat = BatteryConfiguration()
            db.add(db_bat)

        b = update_data.battery
        if b.min_soc > b.max_soc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Battery min_soc cannot exceed max_soc"
            )
        db_bat.capacity_kwh = b.capacity_kwh
        db_bat.initial_soc = b.initial_soc
        db_bat.min_soc = b.min_soc
        db_bat.max_soc = b.max_soc
        db_bat.max_charge_kw = b.max_charge_kw
        db_bat.max_discharge_kw = b.max_discharge_kw
        db_bat.charge_efficiency = b.charge_efficiency
        db_bat.discharge_efficiency = b.discharge_efficiency
        db_bat.updated_at = now

    # 2. Update Grid
    if update_data.grid:
        db_grid = db.query(GridConfiguration).filter(GridConfiguration.is_active == True).first()
        if not db_grid:
            db_grid = GridConfiguration()
            db.add(db_grid)

        g = update_data.grid
        db_grid.import_limit_kw = g.import_limit_kw
        db_grid.export_limit_kw = g.export_limit_kw
        db_grid.import_tariff = g.import_tariff
        db_grid.export_tariff = g.export_tariff
        db_grid.updated_at = now

    # 3. Update PV
    if update_data.pv:
        pv_setting = db.query(SystemSetting).filter(SystemSetting.key == "pv_config").first()
        if not pv_setting:
            pv_setting = SystemSetting(key="pv_config", description="PV configuration")
            db.add(pv_setting)
        pv_setting.value = json.dumps(update_data.pv.model_dump())
        pv_setting.updated_at = now

    # 4. Update Forecast
    if update_data.forecast:
        fc_setting = db.query(SystemSetting).filter(SystemSetting.key == "forecast_config").first()
        if not fc_setting:
            fc_setting = SystemSetting(key="forecast_config", description="Forecast configuration")
            db.add(fc_setting)
        fc_setting.value = json.dumps(update_data.forecast.model_dump())
        fc_setting.updated_at = now

    db.commit()
    return get_all_settings(db=db, current_user=current_user)
