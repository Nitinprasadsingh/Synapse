import pytest


def test_system_health(client):
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_auth_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Admin@123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "admin"


def test_auth_login_invalid(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "WrongPassword"}
    )
    assert response.status_code == 401


def test_auth_me(client, admin_headers):
    response = client.get("/api/v1/auth/me", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@test.com"
    assert data["role"] == "admin"


def test_dashboard_overview(client, analyst_headers):
    response = client.get("/api/v1/dashboard/overview", headers=analyst_headers)
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "energy_flow" in data
    assert "series" in data
    assert len(data["series"]) == 24


def test_forecasts_pv(client, analyst_headers):
    response = client.get("/api/v1/forecasts/pv?horizon=24", headers=analyst_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["forecast_points"]) == 24
    assert data["is_simulated"] is True


def test_forecasts_load(client, analyst_headers):
    response = client.get("/api/v1/forecasts/load?horizon=24", headers=analyst_headers)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert data["summary"]["expected_peak_kw"] > 0


def test_forecasts_combined(client, analyst_headers):
    response = client.get("/api/v1/forecasts/combined?horizon=24", headers=analyst_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["points"]) == 24
    pt = data["points"][0]
    assert round(pt["net_power_kw"], 2) == round(pt["pv_kw"] - pt["load_kw"], 2)


def test_battery_status_and_schedule(client, operator_headers):
    res_status = client.get("/api/v1/battery/status", headers=operator_headers)
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert "capacity_kwh" in status_data
    assert "current_soc" in status_data

    res_gen = client.post(
        "/api/v1/battery/schedule/generate",
        json={"horizon_hours": 24},
        headers=operator_headers
    )
    assert res_gen.status_code == 200
    sched_data = res_gen.json()
    assert len(sched_data["steps"]) == 24
    for step in sched_data["steps"]:
        assert step["soc_after"] >= status_data["min_soc"] - 0.01
        assert step["soc_after"] <= status_data["max_soc"] + 0.01


def test_grid_analytics_and_comparison(client, analyst_headers):
    response = client.get("/api/v1/grid/analytics", headers=analyst_headers)
    assert response.status_code == 200
    data = response.json()
    assert "strategy_comparison" in data
    comp = data["strategy_comparison"]
    assert "baseline_strategy" in comp
    assert "scheduled_strategy" in comp
    assert comp["cost_savings_amount"] >= 0


def test_alerts_lifecycle(client, operator_headers):
    res_list = client.get("/api/v1/alerts", headers=operator_headers)
    assert res_list.status_code == 200
    alerts = res_list.json()
    assert len(alerts) > 0

    first_id = alerts[0]["id"]
    res_ack = client.post(f"/api/v1/alerts/{first_id}/acknowledge", headers=operator_headers)
    assert res_ack.status_code == 200
    assert res_ack.json()["is_acknowledged"] is True


def test_settings_validation(client, admin_headers):
    res_invalid = client.put(
        "/api/v1/settings",
        json={
            "battery": {
                "capacity_kwh": 100,
                "initial_soc": 50,
                "min_soc": 80,
                "max_soc": 20,
                "max_charge_kw": 30,
                "max_discharge_kw": 30,
                "charge_efficiency": 0.9,
                "discharge_efficiency": 0.9
            }
        },
        headers=admin_headers
    )
    assert res_invalid.status_code in [400, 422]
