import io
import csv
import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_analyst
from app.models.user import User
from app.models.measurement import EnergyReport
from app.simulation.mock_engine import simulation_engine
from app.schemas.analytics import (
    EnergyAnalyticsSummary,
    DailyEnergyItem,
    BatteryCyclingStats
)

router = APIRouter()


def _generate_historical_days(days: int = 7) -> List[DailyEnergyItem]:
    """Generate deterministic simulated 7-day or 30-day daily energy records."""
    today = datetime.now(timezone.utc).date()
    items = []
    base_pv = [310.2, 345.8, 380.1, 290.4, 360.5, 335.2, 342.5]
    base_load = [450.5, 470.2, 490.8, 440.1, 480.9, 465.3, 480.2]

    for i in range(days):
        day_date = today - timedelta(days=(days - 1 - i))
        idx = i % len(base_pv)
        pv = base_pv[idx]
        load = base_load[idx]
        bat_ch = round(pv * 0.28, 1)
        bat_dis = round(bat_ch * 0.90, 1)
        grid_imp = round(load - (pv - bat_ch) - bat_dis, 1)
        grid_exp = round(max(0.0, (pv - load) * 0.3), 1)
        net_c = round(grid_imp * 0.15 - grid_exp * 0.08, 2)
        ren_pct = round(((pv - grid_exp) / load) * 100.0, 1)

        items.append(
            DailyEnergyItem(
                date=day_date.isoformat(),
                pv_generation_kwh=pv,
                load_consumption_kwh=load,
                battery_charge_kwh=bat_ch,
                battery_discharge_kwh=bat_dis,
                grid_import_kwh=max(0.0, grid_imp),
                grid_export_kwh=grid_exp,
                net_cost=net_c,
                renewable_utilization_pct=min(100.0, ren_pct),
                peak_demand_kw=round(load / 14.0, 1)
            )
        )
    return items


@router.get("/summary", response_model=EnergyAnalyticsSummary)
def get_analytics_summary(
    period: str = Query("7d", pattern="^(7d|30d)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Retrieve aggregated energy performance metrics and daily time-series.
    """
    days = 30 if period == "30d" else 7
    daily_items = _generate_historical_days(days)

    total_pv = sum(d.pv_generation_kwh for d in daily_items)
    total_load = sum(d.load_consumption_kwh for d in daily_items)
    total_charge = sum(d.battery_charge_kwh for d in daily_items)
    total_discharge = sum(d.battery_discharge_kwh for d in daily_items)
    total_import = sum(d.grid_import_kwh for d in daily_items)
    total_export = sum(d.grid_export_kwh for d in daily_items)
    total_cost = sum(d.net_cost for d in daily_items)
    avg_ren = round(sum(d.renewable_utilization_pct for d in daily_items) / len(daily_items), 1)
    peak_demand = max(d.peak_demand_kw for d in daily_items)

    # Battery cycling statistics
    # 1 full cycle = 100 kWh throughput
    eq_cycles = round(total_discharge / 100.0, 2)
    battery_stats = BatteryCyclingStats(
        equivalent_full_cycles=eq_cycles,
        total_energy_throughput_kwh=round(total_charge + total_discharge, 2),
        average_depth_of_discharge_pct=64.2,
        estimated_soh_pct=98.5
    )

    return EnergyAnalyticsSummary(
        status_label="SIMULATED DATA",
        period=period,
        total_pv_kwh=round(total_pv, 1),
        total_load_kwh=round(total_load, 1),
        total_battery_charge_kwh=round(total_charge, 1),
        total_battery_discharge_kwh=round(total_discharge, 1),
        total_grid_import_kwh=round(total_import, 1),
        total_grid_export_kwh=round(total_export, 1),
        total_energy_cost=round(total_cost, 2),
        renewable_utilization_pct=avg_ren,
        peak_demand_kw=peak_demand,
        battery_stats=battery_stats,
        daily_breakdown=daily_items
    )


@router.get("/energy")
def get_energy_analytics(
    period: str = Query("7d"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    summary = get_analytics_summary(period=period, db=db, current_user=current_user)
    return {
        "period": period,
        "pv_kwh": summary.total_pv_kwh,
        "load_kwh": summary.total_load_kwh,
        "battery_charge_kwh": summary.total_battery_charge_kwh,
        "battery_discharge_kwh": summary.total_battery_discharge_kwh,
        "grid_import_kwh": summary.total_grid_import_kwh,
        "grid_export_kwh": summary.total_grid_export_kwh,
        "breakdown": summary.daily_breakdown
    }


@router.get("/cost")
def get_cost_analytics(
    period: str = Query("7d"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    summary = get_analytics_summary(period=period, db=db, current_user=current_user)
    return {
        "period": period,
        "total_cost": summary.total_energy_cost,
        "breakdown": [
            {"date": d.date, "cost": d.net_cost, "import_kwh": d.grid_import_kwh, "export_kwh": d.grid_export_kwh}
            for d in summary.daily_breakdown
        ]
    }


@router.get("/reports")
def get_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    reports = db.query(EnergyReport).order_by(EnergyReport.created_at.desc()).all()
    return reports


@router.get("/export")
def export_analytics_data(
    format: str = Query("json", pattern="^(json|csv)$"),
    period: str = Query("7d"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Export micro-grid performance dataset in CSV or JSON format.
    """
    summary = get_analytics_summary(period=period, db=db, current_user=current_user)

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Date", "PV Generation (kWh)", "Load Consumption (kWh)",
            "Battery Charge (kWh)", "Battery Discharge (kWh)",
            "Grid Import (kWh)", "Grid Export (kWh)",
            "Net Cost ($)", "Renewable Utilization (%)", "Peak Demand (kW)"
        ])
        for row in summary.daily_breakdown:
            writer.writerow([
                row.date, row.pv_generation_kwh, row.load_consumption_kwh,
                row.battery_charge_kwh, row.battery_discharge_kwh,
                row.grid_import_kwh, row.grid_export_kwh,
                row.net_cost, row.renewable_utilization_pct, row.peak_demand_kw
            ])
        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=microgrid_energy_report_{period}.csv"}
        )
    else:
        return Response(
            content=summary.model_dump_json(indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=microgrid_energy_report_{period}.json"}
        )
