# Synapse: AI-Driven Micro-Grid Load Balancing and Solar Energy Forecasting

Synapse is a micro-grid monitoring and decision-support platform that combines
solar/load forecasting with battery scheduling and an authenticated web
dashboard.

The project is organized as three cooperating services:

1. **AI and optimization service** - Python forecasting, Pyomo/HiGHS
   optimization, model inference, and simulation APIs.
2. **Dashboard backend** - FastAPI orchestration API, authentication,
   persistence, response normalization, and AI-service integration.
3. **Dashboard frontend** - Next.js 14 web application for forecasts, energy
   flow, battery status, grid analytics, alerts, and settings.

> **Data and model scope:** The included datasets and saved model artifacts are
> historical/offline replay assets. The resulting load profile is a simulated
> representative micro-grid profile, not measured building demand. Production
> deployment requires a live weather and metering data adapter.

## Architecture

```text
+---------------------+       +----------------------+
| Next.js dashboard   |------>| FastAPI backend      |
| http://localhost:3000|       | http://localhost:8000|
+---------------------+       +----------+-----------+
                                          |
                                          | HTTP
                                          v
                                +----------------------+
                                | AI service           |
                                | http://localhost:8100|
                                | XGBoost + Pyomo/HiGHS|
                                +----------------------+
                                          |
                                          v
                                Forecast/model artifacts
                                and optimization schedules
```

The browser communicates only with the backend. The backend calls the AI
service and converts its results into the stable dashboard response schemas.
If the AI service is unavailable, the backend can use its explicitly labeled
offline fallback for development and tests.

## Repository layout

```text
.
|-- Dashboard-Application/
|   |-- backend/              FastAPI API, database models, auth, integration
|   |-- frontend/             Next.js dashboard
|   |-- docker-compose.yml    PostgreSQL + backend + frontend
|   `-- microgrid.db          Local SQLite development database
|-- MicroGrid-Integration/
|   |-- battery_optimization/ Forecasting and optimization Python package
|   |-- notebooks/            Datasets, notebooks, and saved model artifacts
|   `-- requirements.txt
|-- integration_docs/
|   |-- API_CONTRACT.md       Cross-service routes and data contract
|   |-- PROJECT_ANALYSIS.md   Architecture and implementation notes
|   `-- RUNBOOK.md            Detailed local runbook
`-- README.md
```

## Prerequisites

- Python 3.11 or newer
- Node.js 18 or newer
- npm
- Docker Desktop (optional, for PostgreSQL and containerized dashboard)

## Quick start: local development

The following starts all three services in separate PowerShell terminals.

### 1. Start the AI service

```powershell
cd MicroGrid-Integration
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn battery_optimization.api:app --host 0.0.0.0 --port 8100
```

Verify it:

```powershell
Invoke-RestMethod http://127.0.0.1:8100/health
```

### 2. Start the backend

```powershell
cd Dashboard-Application\backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The default `.env` uses SQLite and connects to the AI service at
`http://127.0.0.1:8100`. The backend creates and seeds the local database on
startup.

Backend API documentation is available at
`http://127.0.0.1:8000/docs`.

### 3. Start the frontend

```powershell
cd Dashboard-Application\frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000), then sign in using one of
the development accounts below.

## Development accounts

These accounts are seeded for local development only:

| Role | Email | Password |
|---|---|---|
| Administrator | `admin@microgrid.io` | `Admin@12345` |
| Operator | `operator@microgrid.io` | `Operator@12345` |
| Analyst | `analyst@microgrid.io` | `Analyst@12345` |

Change all default credentials and the JWT secret before deploying anywhere
outside a local development environment.

## Configuration

### Backend

Copy `Dashboard-Application/backend/.env.example` to `.env` and configure:

```env
DATABASE_URL=sqlite:///./microgrid.db
AI_SERVICE_URL=http://127.0.0.1:8100
AI_SERVICE_TIMEOUT_SECONDS=30
AI_SIMULATION_START_TIME=2019-01-08T00:00:00Z
```

The default replay start time is within the coverage of the shipped artifacts.
All timestamps at the service boundary are ISO-8601 UTC strings. Model calendar
features and tariffs use the `America/Phoenix` timezone.

### Frontend

Set the backend API base URL in
`Dashboard-Application/frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### AI service

The AI service accepts micro-grid settings through environment variables such
as `MICROGRID_PV_CAPACITY_KW`, `MICROGRID_BATTERY_CAPACITY_KWH`,
`MICROGRID_INITIAL_SOC_PERCENT`, and
`MICROGRID_OPTIMIZATION_HORIZON_HOURS`. See
`MicroGrid-Integration/.env.example` for the complete list.

## Docker

The dashboard compose stack starts:

- PostgreSQL on port `5432`
- Backend on port `8000`
- Frontend on port `3000`

From `Dashboard-Application`:

```powershell
docker compose up --build
```

The current compose file does **not** include the AI service. Start the AI
service separately on the host and configure the backend's
`AI_SERVICE_URL`, or add it as a separate deployment service.

## Main API routes

### AI service (`:8100`)

- `GET /health`
- `GET /config`
- `POST /config`
- `POST /forecast/generate`
- `POST /optimization/simulate`
- `GET /optimization/schedule`
- `GET /optimization/metrics`
- `GET /optimization/baselines`
- `GET /optimization/status`

### Dashboard backend (`:8000`)

- `POST /api/v1/auth/login`
- `GET /api/v1/dashboard/overview`
- `GET /api/v1/dashboard/energy-flow`
- `GET /api/v1/dashboard/kpis`
- `GET /api/v1/forecasts/pv?horizon=24`
- `GET /api/v1/forecasts/load?horizon=24`
- `GET /api/v1/forecasts/combined?horizon=24`
- `GET /api/v1/battery/status`
- `GET /api/v1/battery/schedule`
- `POST /api/v1/battery/schedule/generate`
- `GET /api/v1/grid/status`
- `GET /api/v1/analytics/summary`
- `GET /api/v1/system/health`

See [`integration_docs/API_CONTRACT.md`](integration_docs/API_CONTRACT.md) for
request/response details and unit conventions.

## Testing and validation

Run backend tests:

```powershell
cd Dashboard-Application\backend
.\.venv\Scripts\python.exe -m pytest
```

Run AI-service tests:

```powershell
cd MicroGrid-Integration
.\.venv\Scripts\python.exe -m pytest
```

Build the frontend:

```powershell
cd Dashboard-Application\frontend
npm run build
```

Useful health checks:

```powershell
Invoke-RestMethod http://127.0.0.1:8100/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/system/health
```

## Operational behavior and limitations

- Forecasts use saved Open-Meteo PV and county-demand XGBoost artifacts.
- The load forecast is converted from MW to kW and peak-normalized to a
  simulated representative micro-grid profile.
- Battery dispatch uses a Pyomo mixed-integer optimization model and rolling
  MPC scheduling with HiGHS.
- The NSRDB notebook and artifacts are retained as a historical benchmark and
  are not used for operational inference.
- If the AI service cannot be reached, backend results are labeled
  `OFFLINE FALLBACK / SIMULATED DATA`; they must not be interpreted as live
  model output.
- The system is designed for hourly replay and scheduling. Live operational
  forecasting requires real-time data ingestion, credentials, monitoring, and
  production secret management.

## Further documentation

- [`integration_docs/RUNBOOK.md`](integration_docs/RUNBOOK.md) - step-by-step
  local setup and service startup
- [`integration_docs/API_CONTRACT.md`](integration_docs/API_CONTRACT.md) -
  integration endpoints, units, timestamps, and fallback behavior
- [`integration_docs/PROJECT_ANALYSIS.md`](integration_docs/PROJECT_ANALYSIS.md) -
  architecture and implementation analysis
- [`integration_docs/INTEGRATION_REPORT.md`](integration_docs/INTEGRATION_REPORT.md) -
  integration work and validation summary
