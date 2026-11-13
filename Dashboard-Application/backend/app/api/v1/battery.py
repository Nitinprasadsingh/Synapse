from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_analyst, require_operator
from app.models.user import User
from app.models.battery import BatteryConfiguration, BatterySchedule, BatteryScheduleStep
from app.simulation.mock_engine import simulation_engine
from app.schemas.battery import (
    BatteryConfigSchema,
    BatteryConfigUpdate,
    BatteryStatusResponse,
    BatteryScheduleResponse,
    BatteryScheduleGenerateRequest
)

router = APIRouter()


def _persist_schedule(db: Session, schedule: BatteryScheduleResponse) -> None:
    record = BatterySchedule(
        schedule_id=schedule.schedule_id,
        generated_at=schedule.generated_at,
        status=schedule.status,
        total_cost=schedule.total_cost,
        algorithm=schedule.algorithm,
        is_simulated=schedule.is_simulated,
        notes=schedule.notes,
    )
    record.steps = [
        BatteryScheduleStep(
            step_index=step.step_index,
            timestamp=step.timestamp,
            pv_forecast_kw=step.pv_forecast_kw,
            load_forecast_kw=step.load_forecast_kw,
            action=step.action,
            battery_power_kw=step.battery_power_kw,
            soc_before=step.soc_before,
            soc_after=step.soc_after,
            grid_import_kw=step.grid_import_kw,
            grid_export_kw=step.grid_export_kw,
            step_cost=step.step_cost,
        )
        for step in schedule.steps
    ]
    db.add(record)
    db.commit()


@router.get("/status", response_model=BatteryStatusResponse)
def get_battery_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Get live battery status, SOC, operational limits, mode, and health.
    """
    sim_data = simulation_engine.get_current_dashboard_data(db)
    flow = sim_data["energy_flow"]
    bat_cfg, _, _ = simulation_engine.get_effective_configs(db)

    mode = "IDLE"
    if flow.battery_power_kw > 0.1:
        mode = "CHARGING"
    elif flow.battery_power_kw < -0.1:
        mode = "DISCHARGING"

    op_status = "NORMAL"
    if flow.battery_soc_pct <= bat_cfg.min_soc + 2.0:
        op_status = "WARNING"

    return BatteryStatusResponse(
        capacity_kwh=bat_cfg.capacity_kwh,
        current_soc=flow.battery_soc_pct,
        min_soc=bat_cfg.min_soc,
        max_soc=bat_cfg.max_soc,
        max_charge_kw=bat_cfg.max_charge_kw,
        max_discharge_kw=bat_cfg.max_discharge_kw,
        charge_efficiency=bat_cfg.charge_efficiency,
        discharge_efficiency=bat_cfg.discharge_efficiency,
        battery_health=bat_cfg.battery_health,
        current_power_kw=flow.battery_power_kw,
        mode=mode,
        operational_status=op_status,
        status_label="SIMULATED STATUS"
    )


@router.get("/config", response_model=BatteryConfigSchema)
def get_battery_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Get current battery physical and operational parameters.
    """
    bat_cfg, _, _ = simulation_engine.get_effective_configs(db)
    return bat_cfg


@router.put("/config", response_model=BatteryConfigSchema)
def update_battery_config(
    update_data: BatteryConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """
    Update battery parameters. Validates SOC bounds and persists to database.
    """
    db_bat = db.query(BatteryConfiguration).filter(BatteryConfiguration.is_active == True).first()
    if not db_bat:
        db_bat = BatteryConfiguration()
        db.add(db_bat)

    # Apply updates
    data = update_data.model_dump(exclude_unset=True)
    for field, val in data.items():
        setattr(db_bat, field, val)

    # Validate min_soc <= max_soc
    if db_bat.min_soc > db_bat.max_soc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum SOC cannot exceed Maximum SOC"
        )

    db.commit()
    db.refresh(db_bat)
    return db_bat


@router.get("/schedule", response_model=BatteryScheduleResponse)
def get_battery_schedule(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Retrieve the current 24-hour battery dispatch schedule.
    """
    sim_state = simulation_engine.get_simulation_state(db)
    return sim_state["schedule"]


@router.post("/schedule/generate", response_model=BatteryScheduleResponse)
def generate_battery_schedule(
    request: BatteryScheduleGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """
    Trigger generation of a new 24-hour battery schedule using the simulated dispatch algorithm.
    """
    if request.horizon_hours == 24 and request.custom_initial_soc is None:
        schedule = simulation_engine.get_simulation_state(db)["schedule"]
        _persist_schedule(db, schedule)
        return schedule

    bat_cfg, grid_cfg, _ = simulation_engine.get_effective_configs(db)
    sim_state = simulation_engine.get_simulation_state(db)
    schedule = simulation_engine.battery_optimizer.generate_schedule(
        pv_forecast=sim_state["pv_forecast"],
        load_forecast=sim_state["load_forecast"],
        battery_config=bat_cfg,
        grid_config=grid_cfg,
        current_soc=request.custom_initial_soc or bat_cfg.initial_soc,
        horizon_hours=request.horizon_hours,
    )
    _persist_schedule(db, schedule)
    return schedule
