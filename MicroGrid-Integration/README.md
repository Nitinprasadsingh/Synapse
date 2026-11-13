# AI-Driven Microgrid Optimization

This project integrates the saved Open-Meteo PV XGBoost model and Maricopa
County load XGBoost model with a Pyomo/HiGHS battery scheduler.

The county forecast is converted from MW to kW and then peak-normalized to an
explicitly **simulated** 80 kW representative microgrid profile. It is not
measured building demand. The NSRDB notebook remains a historical benchmark
and is not used operationally.

## Run offline

```powershell
python -m battery_optimization.main
```

Outputs are written to `outputs/optimized_schedule.csv` and
`outputs/optimization_metrics.json`.

## API

```powershell
uvicorn battery_optimization.api:app --reload
```

The dashboard can call `/health`, `/config`, `/forecast/generate`, and
`/optimization/simulate`; results are available from `/optimization/schedule`
and `/optimization/metrics`.

All timestamps are hourly UTC at the integration boundary and are converted
to `America/Phoenix` only for model calendar features and tariffs.
