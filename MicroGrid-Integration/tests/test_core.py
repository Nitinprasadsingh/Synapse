import pandas as pd
import pytest

from battery_optimization.config import MicrogridConfig, ScalingConfig
from battery_optimization.evaluation import validate_energy_balance
from battery_optimization.forecast_integration import ForecastIntegrationService
from battery_optimization.main import optimizer_config
from battery_optimization.optimizer import BatteryOptimizer


def test_default_config_and_scaling():
    config = MicrogridConfig()
    config.validate()
    assert config.scaling.scale_mw_to_kw(config.scaling.reference_max_mw) == 80.0


def test_synthetic_optimizer_balance_and_soc():
    config = MicrogridConfig()
    optimizer = BatteryOptimizer(optimizer_config(config))
    result = optimizer.optimize(
        pv_forecast_kw=[0.0] * 24,
        load_forecast_kw=[20.0] * 24,
        import_tariffs=[0.10] * 24,
        initial_soc_kwh=100.0,
    )
    schedule = pd.DataFrame(result["schedule"])
    assert result["status"] == "optimal"
    assert (schedule["charge_kw"] * schedule["discharge_kw"] == 0).all()
    assert schedule["soc_kwh"].between(20.0, 180.0).all()


def test_generated_schedule_energy_balance():
    schedule = pd.read_csv("outputs/optimized_schedule.csv")
    valid, residual, violations = validate_energy_balance(schedule)
    assert valid
    assert residual <= 1e-4
    assert violations.empty


def test_invalid_configuration_is_rejected():
    with pytest.raises(ValueError, match="min_soc_percent"):
        MicrogridConfig(min_soc_percent=95.0, max_soc_percent=90.0).validate()


def test_scaling_methods_and_units():
    assert ScalingConfig(method="factor", scale_factor=0.001).scale_mw_to_kw(10.0) == 10.0
    with pytest.raises(ValueError):
        ScalingConfig(method="factor").validate()


def test_forecast_integration_is_hourly_and_aligned():
    config = MicrogridConfig()
    service = ForecastIntegrationService(config)
    forecast = service.get_forecast(pd.Timestamp("2019-01-08T00:00:00Z"), 24)
    timestamps = pd.to_datetime(forecast["timestamps"])
    assert len(forecast["pv_kw"]) == 24
    assert len(forecast["load_kw"]) == 24
    assert timestamps.is_monotonic_increasing
    assert timestamps.to_series().diff().dropna().eq(pd.Timedelta(hours=1)).all()


def test_api_health_and_status_serialization():
    from battery_optimization.api import health, status

    assert health()["status"] == "ok"
    assert status()["state"] in {"idle", "complete", "failed", "running"}
