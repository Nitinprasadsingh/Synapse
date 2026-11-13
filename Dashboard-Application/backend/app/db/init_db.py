import json
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.db.database import Base, engine, SessionLocal
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.models.battery import BatteryConfiguration
from app.models.grid import GridConfiguration
from app.models.settings import SystemSetting
from app.models.model_metadata import ModelMetadata
from app.models.alert import SystemAlert
from app.models.measurement import EnergyReport


def init_db(db: Session = None) -> None:
    """Create all tables and seed required initial data."""
    close_db = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        close_db = True

    try:
        # 1. Seed Users
        admin_user = db.query(User).filter(User.email == settings.DEFAULT_ADMIN_EMAIL).first()
        if not admin_user:
            admin_user = User(
                email=settings.DEFAULT_ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                full_name="System Administrator",
                role="admin",
                is_active=True
            )
            db.add(admin_user)

        operator_user = db.query(User).filter(User.email == settings.DEFAULT_OPERATOR_EMAIL).first()
        if not operator_user:
            operator_user = User(
                email=settings.DEFAULT_OPERATOR_EMAIL,
                hashed_password=get_password_hash(settings.DEFAULT_OPERATOR_PASSWORD),
                full_name="Plant Operations Lead",
                role="operator",
                is_active=True
            )
            db.add(operator_user)

        analyst_user = db.query(User).filter(User.email == settings.DEFAULT_ANALYST_EMAIL).first()
        if not analyst_user:
            analyst_user = User(
                email=settings.DEFAULT_ANALYST_EMAIL,
                hashed_password=get_password_hash(settings.DEFAULT_ANALYST_PASSWORD),
                full_name="Energy Systems Analyst",
                role="analyst",
                is_active=True
            )
            db.add(analyst_user)

        # 2. Seed Battery Configuration
        battery_cfg = db.query(BatteryConfiguration).filter(BatteryConfiguration.is_active == True).first()
        if not battery_cfg:
            battery_cfg = BatteryConfiguration(
                capacity_kwh=100.0,
                initial_soc=55.0,
                min_soc=20.0,
                max_soc=95.0,
                max_charge_kw=30.0,
                max_discharge_kw=30.0,
                charge_efficiency=0.92,
                discharge_efficiency=0.92,
                battery_health=98.5,
                is_active=True
            )
            db.add(battery_cfg)

        # 3. Seed Grid Configuration
        grid_cfg = db.query(GridConfiguration).filter(GridConfiguration.is_active == True).first()
        if not grid_cfg:
            grid_cfg = GridConfiguration(
                import_limit_kw=150.0,
                export_limit_kw=100.0,
                import_tariff=0.15,
                export_tariff=0.08,
                is_active=True
            )
            db.add(grid_cfg)

        # 4. Seed System Settings
        default_settings = [
            ("pv_config", json.dumps({
                "installed_capacity_kw": 50.0,
                "derating_factor": 0.85,
                "system_efficiency": 0.90,
                "pv_model_identifier": "open-meteo-xgboost-v1"
            }), "Solar PV plant operational configuration"),
            ("forecast_config", json.dumps({
                "forecast_horizon_hours": 24,
                "scheduling_horizon_hours": 24,
                "optimization_interval_minutes": 60,
                "forecast_update_interval_minutes": 60
            }), "Forecasting and scheduling horizons")
        ]
        for key, val, desc in default_settings:
            setting_row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
            if not setting_row:
                setting_row = SystemSetting(key=key, value=val, description=desc)
                db.add(setting_row)

        # 5. Seed Model Metadata
        models = [
            ModelMetadata(
                model_id="open-meteo-xgboost-v1",
                model_name="Open-Meteo Operational Solar PV Model",
                model_type="pv_forecast",
                version="1.2.0",
                description="Gradient boosted regression trees (XGBoost) trained on GHI, DNI, ambient temperature, and cloud cover features.",
                status="OPERATIONAL (SIMULATED)",
                source="Open-Meteo API + XGBoost",
                metrics_json=json.dumps({"MAE": "1.82 kW", "RMSE": "2.94 kW", "R2": "0.932"}),
                is_simulated=True
            ),
            ModelMetadata(
                model_id="nsrdb-xgboost-benchmark",
                model_name="NSRDB Historical Benchmark Model",
                model_type="pv_forecast",
                version="1.0.0",
                description="Benchmark model trained on 10-year NSRDB satellite irradiance archives for seasonal baseline comparison.",
                status="BENCHMARK (SIMULATED)",
                source="NREL NSRDB Archive",
                metrics_json=json.dumps({"MAE": "2.41 kW", "RMSE": "3.85 kW", "R2": "0.895"}),
                is_simulated=True
            ),
            ModelMetadata(
                model_id="lstm-load-forecaster-v1",
                model_name="Recurrent LSTM Microgrid Load Forecaster",
                model_type="load_forecast",
                version="1.1.0",
                description="Long Short-Term Memory neural network capturing 24-hour diurnal patterns, weekday effects, and climatic demand shifts.",
                status="OPERATIONAL (SIMULATED)",
                source="Campus Substation SCADA",
                metrics_json=json.dumps({"MAPE": "4.85%", "RMSE": "2.12 kW"}),
                is_simulated=True
            ),
            ModelMetadata(
                model_id="heuristic-rule-engine-v1",
                model_name="Microgrid Heuristic Dispatch Engine",
                model_type="battery_opt",
                version="1.0.0",
                description="Deterministic physical energy balancing rule engine. Placeholder for upcoming OR-Tools / MPC optimization engine.",
                status="MOCK (SIMULATED)",
                source="Internal Heuristic Provider",
                metrics_json=json.dumps({"Status": "Active Mock Engine", "OR_Tools_Ready": True}),
                is_simulated=True
            )
        ]
        for m in models:
            existing = db.query(ModelMetadata).filter(ModelMetadata.model_id == m.model_id).first()
            if not existing:
                db.add(m)

        # 6. Seed Alerts
        now = datetime.now(timezone.utc)
        alerts_seed = [
            SystemAlert(
                title="Forecast Sync Complete",
                message="Operational solar forecast updated with Open-Meteo 24-hour meteorological horizon.",
                category="PV",
                severity="INFO",
                is_acknowledged=True,
                acknowledged_at=now - timedelta(hours=2),
                acknowledged_by="operator@microgrid.io",
                timestamp=now - timedelta(hours=2, minutes=15)
            ),
            SystemAlert(
                title="Battery Low SOC Caution",
                message="Battery reached 24.5% SOC during morning peak demand. Approaching 20% minimum SOC threshold.",
                category="Battery",
                severity="WARNING",
                is_acknowledged=False,
                timestamp=now - timedelta(minutes=45)
            ),
            SystemAlert(
                title="Grid Export Interconnection Active",
                message="Net solar generation surplus currently backfeeding to regional distribution feeder.",
                category="Grid",
                severity="INFO",
                is_acknowledged=False,
                timestamp=now - timedelta(minutes=10)
            )
        ]
        if db.query(SystemAlert).count() == 0:
            for a in alerts_seed:
                db.add(a)

        # 7. Seed Energy Reports
        if db.query(EnergyReport).count() == 0:
            daily_report = EnergyReport(
                report_type="daily",
                period_start=now - timedelta(days=1),
                period_end=now,
                total_pv_kwh=342.5,
                total_load_kwh=480.2,
                total_battery_charge_kwh=92.4,
                total_battery_discharge_kwh=88.1,
                total_grid_import_kwh=165.8,
                total_grid_export_kwh=28.3,
                total_cost=22.61,
                renewable_utilization_pct=65.5,
                peak_grid_kw=42.1
            )
            db.add(daily_report)

        db.commit()
        print("Database initialized and seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error during db initialization: {e}")
        raise e
    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    init_db()
