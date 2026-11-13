# API contract

The browser calls the backend at `NEXT_PUBLIC_API_URL`. The backend calls the
Python AI service at `AI_SERVICE_URL`; the browser never calls Python directly.
All integration timestamps are ISO-8601 UTC strings. Model calendar features
and tariffs use `America/Phoenix`.

## AI service

| Method | Route | Request | Response |
|---|---|---|---|
| GET | `/health` | none | `{status, solver}` |
| GET | `/config` | none | validated microgrid configuration |
| POST | `/config` | partial configuration | updated configuration |
| POST | `/forecast/generate` | `{start_time, horizon_hours}` | `{timestamps, pv_kw, load_kw}` |
| POST | `/optimization/simulate` | `{start_time, horizon_hours}` | `{metrics, schedule, solver_statuses}` |
| GET | `/optimization/schedule` | none | `{schedule}` |
| GET | `/optimization/metrics` | none | metrics |
| GET | `/optimization/baselines` | none | baseline metrics |
| GET | `/optimization/status` | none | execution status |

`pv_kw` and `load_kw` are kW. Battery power and grid power are kW; SOC in the
AI schedule is kWh, while the dashboard schedule contract uses SOC percent.
Costs are currency per hourly step and total currency for a schedule.

## Backend dashboard routes

Existing authenticated routes remain stable:

- `GET /api/v1/dashboard/overview`
- `GET /api/v1/dashboard/energy-flow`
- `GET /api/v1/dashboard/kpis`
- `GET /api/v1/forecasts/pv?horizon=24`
- `GET /api/v1/forecasts/load?horizon=24`
- `GET /api/v1/forecasts/combined?horizon=24`
- `GET /api/v1/battery/status`
- `GET /api/v1/battery/schedule`
- `POST /api/v1/battery/schedule/generate`

The backend normalizes AI results into the existing frontend schemas:

```json
{
  "timestamp": "2019-01-08T00:00:00Z",
  "pv_forecast_kw": 0.0,
  "load_forecast_kw": 42.0,
  "battery_soc_percent": 50.0,
  "battery_action": "DISCHARGE",
  "battery_power_kw": 12.0,
  "grid_import_kw": 30.0,
  "grid_export_kw": 0.0,
  "predicted_energy_cost": 3.0
}
```

This is a shape example only; values are returned by the saved models and
optimizer. Authentication requirements and error responses are unchanged from
the existing backend routes. AI connection or solver failures are surfaced in
backend logs and the backend uses its clearly labeled offline fallback only
when the AI service cannot be reached.

