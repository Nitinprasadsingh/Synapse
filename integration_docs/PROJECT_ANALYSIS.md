# Project analysis

## Workspace structure

- `MicroGrid-Integration/` is the Python forecasting and optimization project.
- `Dashboard-Application/backend/` is the authenticated FastAPI orchestration API.
- `Dashboard-Application/frontend/` is the Next.js 14 dashboard.
- `Dashboard-Application/microgrid.db` is the local SQLite development database.

## AI and optimization project

The AI project uses Python, pandas, NumPy, scikit-learn, XGBoost, Pyomo, and
HiGHS. Operational PV inference loads the Open-Meteo XGBoost artifact from
`notebooks/open-meteo-model_artifacts`; the NSRDB notebook remains a historical
benchmark. Load inference loads the saved county-demand XGBoost artifact and
converts MW to kW using `ScalingConfig`, then peak-normalizes the result to an
explicit simulated representative microgrid profile.

`ForecastIntegrationService` performs feature engineering, timezone conversion,
lag/rolling load features, timestamp alignment, and forecast merging.
`BatteryOptimizer` implements the Pyomo MILP; `MPCScheduler` runs rolling
optimization; `BaselineEvaluator` produces no-battery and rule-based
comparisons. The existing FastAPI service in `battery_optimization/api.py`
exposes health, configuration, forecast, optimization, schedule, metrics,
baseline, and status routes.

Run from `MicroGrid-Integration`:

```powershell
python -m battery_optimization.main
uvicorn battery_optimization.api:app --host 0.0.0.0 --port 8100
```

The shipped artifacts are historical/offline replay data. A simulation start
time must therefore fall inside the artifact coverage (the default integration
start is `2019-01-08T00:00:00Z`).

## Backend

The backend is FastAPI with SQLAlchemy and JWT authentication. Existing routes
cover authentication, dashboard, forecasts, battery, grid, analytics, alerts,
settings, and system health. Existing database models include users, battery
configuration and schedules, grid configuration, forecasts, measurements,
alerts, settings, and model metadata.

Before integration, dashboard and battery routes called
`app/simulation/mock_engine.py`, which in turn used the mock PV, load, and
heuristic optimization providers. These providers remain available as an
explicit offline fallback when the AI service is unavailable.

## Frontend

The frontend is a Next.js 14 App Router application using React Query,
Recharts, Tailwind, and the existing API client. Dashboard pages and charts
already consume the backend route shapes, so the integration preserves the UI
and replaces the backend's primary data source rather than introducing a
second frontend API.

## Integration gaps found

1. The backend had no AI-service client and always used mock forecasts and
   schedules.
2. The dashboard response labels identified all values as simulated, even
   when real model output was available.
3. There was no environment-controlled AI service URL or historical replay
   start time.
4. The existing schedule persistence model was present but not used by the
   simulation path.
5. API and runbook documentation for the cross-service contract was missing.

