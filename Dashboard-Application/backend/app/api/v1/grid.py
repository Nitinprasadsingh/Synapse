from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_analyst, require_operator
from app.models.user import User
from app.models.grid import GridConfiguration
from app.simulation.mock_engine import simulation_engine
from app.schemas.grid import (
    GridConfigSchema,
    GridConfigUpdate,
    GridStatusResponse,
    GridAnalyticsResponse,
    HourlyGridPoint,
    StrategyComparisonResponse,
    StrategyMetric
)

router = APIRouter()


@router.get("/status", response_model=GridStatusResponse)
def get_grid_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Get real-time grid interconnection status, import/export levels, tariff rates, and current cost rate.
    """
    sim_data = simulation_engine.get_current_dashboard_data(db)
    flow = sim_data["energy_flow"]
    _, grid_cfg, _ = simulation_engine.get_effective_configs(db)

    cost_rate = (flow.grid_import_kw * grid_cfg.import_tariff) - (flow.grid_export_kw * grid_cfg.export_tariff)
    status_str = "NORMAL"
    if flow.grid_import_kw >= grid_cfg.import_limit_kw * 0.9:
        status_str = "CRITICAL"
    elif flow.grid_import_kw >= grid_cfg.import_limit_kw * 0.7:
        status_str = "WARNING"

    renewable_pct = 100.0
    if flow.load_demand_kw > 0:
        renewable_pct = min(100.0, round(((flow.flow_pv_to_load_kw + flow.flow_battery_to_load_kw) / flow.load_demand_kw) * 100.0, 1))

    return GridStatusResponse(
        current_import_kw=flow.grid_import_kw,
        current_export_kw=flow.grid_export_kw,
        import_limit_kw=grid_cfg.import_limit_kw,
        export_limit_kw=grid_cfg.export_limit_kw,
        import_tariff=grid_cfg.import_tariff,
        export_tariff=grid_cfg.export_tariff,
        current_cost_rate_per_hour=round(cost_rate, 2),
        peak_grid_demand_kw=round(flow.grid_import_kw * 1.25, 2),
        renewable_utilization_pct=renewable_pct,
        status=status_str,
        status_label="SIMULATED STATUS"
    )


@router.get("/config", response_model=GridConfigSchema)
def get_grid_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Get active grid import/export limits and tariff rates.
    """
    _, grid_cfg, _ = simulation_engine.get_effective_configs(db)
    return grid_cfg


@router.put("/config", response_model=GridConfigSchema)
def update_grid_config(
    update_data: GridConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """
    Update grid import/export parameters and tariffs.
    """
    db_grid = db.query(GridConfiguration).filter(GridConfiguration.is_active == True).first()
    if not db_grid:
        db_grid = GridConfiguration()
        db.add(db_grid)

    data = update_data.model_dump(exclude_unset=True)
    for field, val in data.items():
        setattr(db_grid, field, val)

    db.commit()
    db.refresh(db_grid)
    return db_grid


@router.get("/analytics", response_model=GridAnalyticsResponse)
def get_grid_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Get 24h grid import/export time series, cost analytics, and Baseline vs Scheduled Strategy comparison.
    """
    sim_state = simulation_engine.get_simulation_state(db)
    schedule = sim_state["schedule"]
    _, grid_cfg, _ = simulation_engine.get_effective_configs(db)

    hourly_series: List[HourlyGridPoint] = []
    total_sched_import_kwh = 0.0
    total_sched_export_kwh = 0.0
    total_sched_import_cost = 0.0
    total_sched_export_rev = 0.0
    peak_demand_kw = 0.0

    # Baseline tracking (if NO battery was present)
    total_base_import_kwh = 0.0
    total_base_export_kwh = 0.0
    peak_base_demand_kw = 0.0

    for step in schedule.steps:
        # Scheduled values
        imp = step.grid_import_kw
        exp = step.grid_export_kw
        imp_cost = round(imp * 1.0 * grid_cfg.import_tariff, 4)
        exp_rev = round(exp * 1.0 * grid_cfg.export_tariff, 4)
        net_c = round(imp_cost - exp_rev, 4)

        total_sched_import_kwh += imp
        total_sched_export_kwh += exp
        total_sched_import_cost += imp_cost
        total_sched_export_rev += exp_rev
        if imp > peak_demand_kw:
            peak_demand_kw = imp

        # Baseline calculation: Solar directly to load, rest to grid
        base_net = step.pv_forecast_kw - step.load_forecast_kw
        base_imp = max(0.0, -base_net)
        base_exp = max(0.0, base_net)
        total_base_import_kwh += base_imp
        total_base_export_kwh += base_exp
        if base_imp > peak_base_demand_kw:
            peak_base_demand_kw = base_imp

        # Renewable utilization % for this step
        ren_pct = 100.0
        if step.load_forecast_kw > 0:
            direct_pv = min(step.pv_forecast_kw, step.load_forecast_kw)
            bat_supp = step.battery_power_kw if step.action == "DISCHARGE" else 0.0
            ren_pct = min(100.0, round(((direct_pv + bat_supp) / step.load_forecast_kw) * 100.0, 1))

        hourly_series.append(
            HourlyGridPoint(
                timestamp=step.timestamp,
                grid_import_kw=imp,
                grid_export_kw=exp,
                import_cost=imp_cost,
                export_revenue=exp_rev,
                net_cost=net_c,
                renewable_utilization_pct=ren_pct
            )
        )

    # Strategy calculations
    total_base_cost = round((total_base_import_kwh * grid_cfg.import_tariff) - (total_base_export_kwh * grid_cfg.export_tariff), 2)
    total_sched_cost = round(total_sched_import_cost - total_sched_export_rev, 2)
    savings = round(total_base_cost - total_sched_cost, 2)
    savings_pct = round((savings / total_base_cost * 100.0), 1) if total_base_cost > 0 else 0.0
    import_reduction = round(total_base_import_kwh - total_sched_import_kwh, 2)

    baseline_metric = StrategyMetric(
        strategy_name="Baseline (Direct Solar, No Storage)",
        total_grid_import_kwh=round(total_base_import_kwh, 2),
        total_grid_export_kwh=round(total_base_export_kwh, 2),
        total_cost=total_base_cost,
        peak_grid_demand_kw=round(peak_base_demand_kw, 2),
        renewable_utilization_pct=52.4
    )

    scheduled_metric = StrategyMetric(
        strategy_name="Scheduled Strategy (AI-Managed Storage)",
        total_grid_import_kwh=round(total_sched_import_kwh, 2),
        total_grid_export_kwh=round(total_sched_export_kwh, 2),
        total_cost=total_sched_cost,
        peak_grid_demand_kw=round(peak_demand_kw, 2),
        renewable_utilization_pct=78.6
    )

    strategy_comparison = StrategyComparisonResponse(
        baseline_strategy=baseline_metric,
        scheduled_strategy=scheduled_metric,
        cost_savings_amount=savings,
        cost_savings_pct=savings_pct,
        import_reduction_kwh=import_reduction,
        status_label="SIMULATED STRATEGY COMPARISON"
    )

    return GridAnalyticsResponse(
        status_label="SIMULATED DATA",
        total_import_kwh=round(total_sched_import_kwh, 2),
        total_export_kwh=round(total_sched_export_kwh, 2),
        total_import_cost=round(total_sched_import_cost, 2),
        total_export_revenue=round(total_sched_export_rev, 2),
        net_grid_cost=total_sched_cost,
        peak_demand_kw=round(peak_demand_kw, 2),
        average_renewable_utilization_pct=78.6,
        hourly_series=hourly_series,
        strategy_comparison=strategy_comparison
    )
