# Local runbook

## Prerequisites

- Python 3.11+ with the AI and backend requirements installed.
- Node.js 18+ with frontend dependencies installed.
- Saved model artifacts under `MicroGrid-Integration/notebooks`.

## Start the services

Open three PowerShell terminals, each in the folder specified below. These
instructions assume the repository has already been cloned locally.

Terminal 1 — open the terminal in the `MicroGrid-Integration` folder:

```powershell
if (-not (Test-Path .\.venv\Scripts\python.exe)) {
    py -3 -m venv .venv
}
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn battery_optimization.api:app --host 0.0.0.0 --port 8100
```

Terminal 2 — open the terminal in the `Dashboard-Application\backend` folder:

```powershell
if (-not (Test-Path .\.venv\Scripts\python.exe)) {
    py -3 -m venv .venv
}
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:AI_SERVICE_URL = "http://127.0.0.1:8100"
$env:AI_SIMULATION_START_TIME = "2019-01-08T00:00:00Z"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Terminal 3 — open the terminal in the `Dashboard-Application\frontend` folder:

```powershell
npm install
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000/api/v1"
npm run dev
```

Open `http://localhost:3000`, sign in with the configured seed account, and
open the dashboard. The dashboard flow is:

`Dashboard -> backend -> AI service -> saved forecasts and MILP/MPC optimizer -> backend schemas/database -> dashboard`.

The local database is SQLite by default. Docker Compose still starts the
existing PostgreSQL-backed backend/frontend stack; run the AI service locally
or add it as a separate service using the same `AI_SERVICE_URL` contract.

## Health and verification

```powershell
Invoke-RestMethod http://127.0.0.1:8100/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/system/health
```

If the AI service is stopped, backend responses are explicitly labeled
`OFFLINE FALLBACK / SIMULATED DATA`; they are not production model outputs.
