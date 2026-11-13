# Integration report

## Implemented

- Documented the discovered AI, backend, frontend, model, database, and
  integration architecture in `PROJECT_ANALYSIS.md`.
- Added the cross-service endpoint, unit, timestamp, and error contract.
- Added a local runbook with separate AI, backend, and frontend commands.
- Connected the backend simulation engine to the existing AI service through a
  configurable HTTP adapter.
- Normalized saved-model forecasts and Pyomo/MPC schedules into the existing
  dashboard response schemas.
- Kept the existing providers as an explicit, labeled offline fallback for
  local tests and environments where the AI process is unavailable.

## Existing components reused

- Open-Meteo XGBoost PV model for operations.
- NSRDB notebook as benchmark-only artifact.
- Saved load XGBoost model, MW-to-kW conversion, and representative scaling.
- Pyomo/HiGHS optimizer, MPC scheduler, and baseline evaluator.
- Existing FastAPI authentication, SQLAlchemy models, routes, React Query
  client, Recharts components, and database.

## Validation

- AI project tests: 7 passed after fixing timezone-aware pandas date-range
  construction for the API scheduler path.
- Backend tests: 12 passed.
- Frontend production build: passed.
- Live AI health and simulation: passed; 24/24 solver statuses were `optimal`.
- Live backend flow: passed; authenticated overview returned 24 live model
  points labeled `LIVE MODEL OUTPUT`.
- Live schedule generation: passed; 24-step `Pyomo HiGHS MPC` output was
  returned and persisted by the backend.
- The historical replay start time used for verification was
  `2019-01-08T00:00:00Z`.

## Known limitations

- The shipped datasets are historical replay data, not live weather or
  metering. Live operational forecasting requires a weather/data acquisition
  adapter with credentials/configuration.
- Docker Compose does not yet include the AI service; the runbook starts it
  separately.
- Offline fallback is retained for deterministic development tests and is
  clearly labeled rather than presented as model output.
