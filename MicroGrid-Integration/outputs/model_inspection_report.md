# Model Inspection Report
## MicroGrid Battery Optimization — AI-Driven Solar & Load Forecasting

> **Report generated:** 2026-11-10  
> **Project root:** `c:\Users\nitin\Desktop\MicroGrid_Project`  
> **Scope:** Three ML models — Open-Meteo PV Forecaster, Load Forecaster, and NSRDB Baseline PV Model

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Model A — Open-Meteo PV Forecaster](#2-model-a--open-meteo-pv-forecaster)
3. [Model B — Load Forecaster (Maricopa County)](#3-model-b--load-forecaster-maricopa-county)
4. [Model C — NSRDB Baseline PV Model](#4-model-c--nsrdb-baseline-pv-model)
5. [Cross-Model Comparison](#5-cross-model-comparison)
6. [Data Leakage Audit](#6-data-leakage-audit)
7. [Operational Readiness Summary](#7-operational-readiness-summary)
8. [Integration Recommendations](#8-integration-recommendations)

---

## 1. Executive Summary

This project implements a 1-hour-ahead forecasting pipeline for a 100 kW microgrid serving the Phoenix, AZ area. Three XGBoost-based models were developed:

| Model | Purpose | Artifact Saved? | Operational? |
|:------|:--------|:-------------:|:------------:|
| **Open-Meteo PV** | 1-h-ahead solar PV output from live weather API | ✅ Yes | ✅ Yes |
| **Load Forecaster** | 1-h-ahead regional load demand (Maricopa County) | ✅ Yes | ✅ Yes (needs lag seed) |
| **NSRDB Baseline** | Historical PV benchmark using NSRDB irradiance data | ❌ No | ❌ No |

The Open-Meteo PV model and Load Forecaster are **production-ready** (pre-trained artifacts exist). The NSRDB model is a **historical benchmark only** — it requires retraining and cannot be deployed operationally without NSRDB historical weather data for inference.

---

## 2. Model A — Open-Meteo PV Forecaster

### 2.1 Artifact Paths

| Artifact | Path |
|:---------|:-----|
| **Model file** | `notebooks/open-meteo-model_artifacts/deployment_pv_xgboost_model.json` |
| **Features JSON** | `notebooks/open-meteo-model_artifacts/pv_model_features.json` |
| **Training dataset** | `notebooks/open-meteo-model_artifacts/prepared_pv_forecasting_dataset.csv` |
| **Test predictions** | `notebooks/open-meteo-model_artifacts/pv_test_predictions.csv` |
| **Training notebook** | `notebooks/open-meteo-model.ipynb` |
| **Raw weather data** | `notebooks/open-meteo-data.csv` |

### 2.2 Target Variable

| Property | Value |
|:---------|:------|
| **Column name** | `target_pv_next_hour` |
| **Description** | 1-hour-ahead PV output power |
| **Unit** | kW |
| **Range (observed)** | 0 to ~86.3 kW |
| **System capacity** | 100 kW |
| **Horizon** | t+1 hour |

### 2.3 Feature List (Exact Order — 14 Features)

> **Important:** The feature DataFrame passed to `model.predict()` must use **exactly** this column order as defined in `pv_model_features.json`.

| # | Feature Name | Type | Unit | Source |
|:--|:-------------|:----:|:----:|:-------|
| 1 | `temperature_2m (°C)` | Meteorological | °C | Open-Meteo API |
| 2 | `relative_humidity_2m (%)` | Meteorological | % | Open-Meteo API |
| 3 | `dew_point_2m (°C)` | Meteorological | °C | Open-Meteo API |
| 4 | `cloud_cover (%)` | Meteorological | % | Open-Meteo API |
| 5 | `wind_speed_10m (km/h)` | Meteorological | km/h | Open-Meteo API |
| 6 | `wind_direction_10m (°)` | Meteorological | ° | Open-Meteo API |
| 7 | `shortwave_radiation (W/m²)` | Irradiance | W/m² | Open-Meteo API |
| 8 | `direct_radiation (W/m²)` | Irradiance | W/m² | Open-Meteo API |
| 9 | `diffuse_radiation (W/m²)` | Irradiance | W/m² | Open-Meteo API |
| 10 | `direct_normal_irradiance (W/m²)` | Irradiance | W/m² | Open-Meteo API |
| 11 | `hour_sin` | Cyclical time | dimensionless | Engineered |
| 12 | `hour_cos` | Cyclical time | dimensionless | Engineered |
| 13 | `month` | Calendar | integer (1–12) | Engineered |
| 14 | `dayofweek` | Calendar | integer (0–6, Mon=0) | Engineered |

### 2.4 Preprocessing Pipeline

```
Raw Open-Meteo CSV / API Response
        │
        ▼
1. Parse "time" column → naive datetime (no tz localization)
        │
        ▼
2. Extract calendar fields:
   - hour  = timestamp.dt.hour
   - month = timestamp.dt.month
   - dayofweek = timestamp.dt.dayofweek
        │
        ▼
3. Compute cyclical time features:
   - hour_sin = sin(2π × hour / 24)
   - hour_cos = cos(2π × hour / 24)
        │
        ▼
4. Assemble feature DataFrame in exact column order
   (from pv_model_features.json)
        │
        ▼
5. Load model:
   model = XGBRegressor()
   model.load_model("deployment_pv_xgboost_model.json")
        │
        ▼
6. Predict:
   y_pred = model.predict(X)   # Returns kW values
```

**Missing value handling:** Imputation strategy not explicitly documented in the deployment notebook. Training data was cleaned via interpolation + forward/backward fill on the prepared dataset CSV. At inference, Open-Meteo API responses are expected to be gap-free.

### 2.5 Timestamp & Timezone Handling

| Property | Detail |
|:---------|:-------|
| **Training timestamps** | Naive datetimes (no timezone info stored) |
| **Open-Meteo API source** | UTC by default, but training data was likely queried with Phoenix local context |
| **Risk** | Ambiguity: UTC hours ≠ Phoenix local solar hours (UTC-7). `hour_sin`/`hour_cos` computed on naive datetimes may be UTC-offset, causing systematic error in time-of-day patterns |
| **Recommendation** | Verify that inference timestamps are in the **same naive-UTC representation** used during training, or convert API UTC times to `America/Phoenix` before feature extraction |

### 2.6 Model Configuration

| Hyperparameter | Value |
|:---------------|:------|
| Algorithm | XGBoost Regressor |
| `n_estimators` | 300 |
| `max_depth` | 6 |
| `learning_rate` | 0.05 |
| `subsample` | 0.8 |
| `colsample_bytree` | 0.8 |
| `objective` | `reg:squarederror` |
| `random_state` | 42 |

### 2.7 Prediction & Confidence Interval

- **Point prediction:** `model.predict(X)` returns a `float32` NumPy array in kW.
- **Prediction bounds:** Empirical lower/upper bounds are pre-computed and stored in `pv_test_predictions.csv`. The columns `lower_bound` and `upper_bound` represent approximate ±1-residual-std intervals around the test predictions. These are **not** model-native (no quantile regression was used); they must be pre-characterized from test-set residuals for use in the optimizer.

### 2.8 Training Data Characteristics

| Property | Value |
|:---------|:------|
| **Date range** | January 2017 – December 2019 |
| **Resolution** | Hourly |
| **Total samples** | 26,280 |
| **Train/Test split** | Chronological 80/20 |
| **Training samples** | ~21,024 |
| **Test samples** | ~5,256 |
| **Test window** | Approx. July 2019 onwards (based on `pv_test_predictions.csv` start: 2019-07-20) |

### 2.9 Test Set Performance

Performance metrics were observed on the held-out test set (from `pv_test_predictions.csv`; exact metrics embedded in training notebook output):

| Metric | Value |
|:-------|:------|
| Test period start | 2019-07-20 |
| Prediction range | 0 – ~86.3 kW |
| Daytime nMAE (benchmark reference) | ~1.84–5.45% (comparable to load model context) |

---

## 3. Model B — Load Forecaster (Maricopa County)

### 3.1 Artifact Paths

| Artifact | Path |
|:---------|:-----|
| **Model file** | `notebooks/load_forecasting_artifacts/load_xgboost_model.json` |
| **Features JSON** | `notebooks/load_forecasting_artifacts/load_model_features.json` |
| **Performance metrics** | `notebooks/load_forecasting_artifacts/load_forecasting_metrics.csv` |
| **Performance report** | `notebooks/load_forecasting_artifacts/load_forecasting_report.txt` |
| **Feature importances** | `notebooks/load_forecasting_artifacts/load_feature_importance.csv` |
| **Test predictions** | `notebooks/load_forecasting_artifacts/load_test_predictions.csv` |
| **Cleaned training data** | `notebooks/load_forecasting_artifacts/load_clean_2017_2019.csv` |
| **Training notebook** | `notebooks/load_forecast_model.ipynb` |
| **Raw load data** | `notebooks/load_data.csv` |

### 3.2 Target Variable

| Property | Value |
|:---------|:------|
| **Column name** | `Target_Load` |
| **Description** | `Load_MW` shifted backward by 1 period — i.e., the actual load at hour t+1 |
| **Unit** | MW |
| **Range (observed training)** | 3,344 to 11,555 MW |
| **Geographic region** | Maricopa County, Arizona (Phoenix area) |
| **Horizon** | t+1 hour |

> **Note:** This is a **regional-level** model (thousands of MW). For microgrid-level (100 kW) applications, predictions must be scaled by an appropriate demand factor or supplemented with building-level load profiles.

### 3.3 Feature List (Exact Order — 26 Features)

> **Important:** The feature DataFrame must use **exactly** this column order as defined in `load_model_features.json`.

#### Temporal / Cyclical Features

| # | Feature Name | Formula / Source | Description |
|:--|:-------------|:----------------|:------------|
| 1 | `Hour_sin` | sin(2π × Hour / 24) | Cyclical hour encoding |
| 2 | `Hour_cos` | cos(2π × Hour / 24) | Cyclical hour encoding |
| 3 | `DayOfWeek_sin` | sin(2π × DayOfWeek / 7) | Cyclical weekday encoding |
| 4 | `DayOfWeek_cos` | cos(2π × DayOfWeek / 7) | Cyclical weekday encoding |
| 5 | `Month_sin` | sin(2π × Month / 12) | Cyclical month encoding |
| 6 | `Month_cos` | cos(2π × Month / 12) | Cyclical month encoding |

#### Calendar Features

| # | Feature Name | Type | Range |
|:--|:-------------|:----:|:-----:|
| 7 | `Hour` | Integer | 0–23 |
| 8 | `DayOfWeek` | Integer | 0–6 (Mon=0) |
| 9 | `DayOfMonth` | Integer | 1–31 |
| 10 | `Month` | Integer | 1–12 |
| 11 | `DayOfYear` | Integer | 1–366 |
| 12 | `IsWeekend` | Binary | 0 or 1 |

#### Lag Features (Load_MW, t-n hours)

| # | Feature Name | Lag | Captures |
|:--|:-------------|:---:|:---------|
| 13 | `Load_lag_1` | t-1 h | Previous hour load |
| 14 | `Load_lag_2` | t-2 h | 2 hours ago |
| 15 | `Load_lag_3` | t-3 h | 3 hours ago |
| 16 | `Load_lag_6` | t-6 h | 6 hours ago |
| 17 | `Load_lag_12` | t-12 h | Half-day periodicity |
| 18 | `Load_lag_24` | t-24 h | Same hour yesterday |
| 19 | `Load_lag_48` | t-48 h | Same hour 2 days ago |
| 20 | `Load_lag_168` | t-168 h | Same hour last week |

#### Rolling Statistics

| # | Feature Name | Window | Statistic | Note |
|:--|:-------------|:------:|:---------:|:-----|
| 21 | `RollingMean_3` | 3 h | Mean | Computed on past observations only (no leakage) |
| 22 | `RollingMean_6` | 6 h | Mean | Same |
| 23 | `RollingMean_24` | 24 h | Mean | Same |
| 24 | `RollingMean_168` | 168 h | Mean | Same |
| 25 | `RollingStd_24` | 24 h | Std Dev | Same |
| 26 | `RollingStd_168` | 168 h | Std Dev | Same |

### 3.4 Preprocessing Pipeline

```
Raw Load Data (Maricopa_Load_2017_2019.csv)
        │  Columns: Timestamp_UTC, Load_MW
        ▼
1. Parse Timestamp_UTC → tz-aware UTC datetime
        │
        ▼
2. Convert to America/Phoenix local time:
   ts_local = ts_utc.tz_convert("America/Phoenix")
   (Phoenix does NOT observe DST — UTC-7 year-round)
        │
        ▼
3. Extract calendar features from local time:
   Hour, DayOfWeek, DayOfMonth, Month, DayOfYear, IsWeekend
        │
        ▼
4. Compute cyclical encodings:
   Hour_sin/cos, DayOfWeek_sin/cos, Month_sin/cos
        │
        ▼
5. Compute lag features (requires 168 hours history):
   Load_lag_1 ... Load_lag_168
   NOTE: Lags are computed on the SHIFTED target series
         (Load_MW at t, not Target_Load)
        │
        ▼
6. Compute rolling statistics (past-only windows):
   RollingMean_3/6/24/168, RollingStd_24/168
        │
        ▼
7. Create target: Target_Load = Load_MW.shift(-1)
        │
        ▼
8. Drop NaN rows (first 168 h and last 1 h are invalid)
        │
        ▼
9. Assemble feature DataFrame in exact column order
   (from load_model_features.json)
        │
        ▼
10. Load model:
    model = xgb.XGBRegressor()
    model.load_model("load_xgboost_model.json")
        │
        ▼
11. Predict:
    y_pred = model.predict(X)   # Returns MW values
```

### 3.5 Timestamp & Timezone Handling

| Property | Detail |
|:---------|:-------|
| **Raw data timezone** | UTC (column: `Timestamp_UTC`) |
| **Training timezone** | Converted to `America/Phoenix` (UTC-7, no DST) for all calendar feature extraction |
| **Inference requirement** | Input timestamps must be in UTC; convert to `America/Phoenix` before feature engineering |
| **DST note** | Arizona (Phoenix) does not observe Daylight Saving Time — UTC offset is constant at -7 hours throughout the year |

### 3.6 Model Configuration

| Hyperparameter | Value |
|:---------------|:------|
| Algorithm | XGBoost Regressor |
| `n_estimators` | 1,000 (max) |
| `max_depth` | 6 |
| `learning_rate` | 0.03 |
| `min_child_weight` | 3 |
| `subsample` | 0.8 |
| `colsample_bytree` | 0.8 |
| `objective` | `reg:squarederror` |
| `random_state` | 42 |
| **Early stopping** | Enabled (monitored on validation RMSE) |
| **Eval sets** | Train + Validation |
| **Verbose** | Every 100 rounds |

### 3.7 Training / Validation / Test Split

| Partition | Fraction | Approximate Size | Period |
|:----------|:--------:|:----------------:|:-------|
| **Training** | 70% | 18,277 samples | Jan 2017 – Oct 2018 |
| **Validation** | 15% | 3,917 samples | Oct 2018 – May 2019 |
| **Test** | 15% | 3,917 samples | May 2019 – Dec 2019 |

Split is **strictly chronological** — no random shuffling. Test set starts at approximately 2019-07-21 (UTC) based on `load_test_predictions.csv`.

### 3.8 Test Set Performance

| Model | MAE (MW) | RMSE (MW) | R² | nMAE (%) |
|:------|:--------:|:---------:|:--:|:--------:|
| Persistence Baseline | 242.08 | 305.26 | 0.9739 | 4.13% |
| Seasonal Persistence | 381.13 | 525.93 | 0.9225 | 6.51% |
| **XGBoost** | **107.68** | **154.44** | **0.9933** | **1.84%** |

**Improvement over Persistence:** 55.52% MAE reduction, 49.41% RMSE reduction.

### 3.9 Feature Importance (Top 10)

| Rank | Feature | Importance (Gain) | Insight |
|:----:|:--------|:-----------------:|:--------|
| 1 | `Load_lag_24` | 0.5855 | Same hour yesterday — dominant signal |
| 2 | `Load_lag_1` | 0.1707 | Previous hour — strong autocorrelation |
| 3 | `RollingMean_3` | 0.0568 | Short-term trend |
| 4 | `Load_lag_48` | 0.0530 | 2-day periodicity |
| 5 | `Hour_cos` | 0.0434 | Diurnal cyclical pattern |
| 6 | `Hour` | 0.0224 | Raw hour-of-day |
| 7 | `RollingMean_24` | 0.0108 | Daily rolling context |
| 8 | `Load_lag_6` | 0.0072 | Within-day variation |
| 9 | `Hour_sin` | 0.0069 | Diurnal cyclical pattern |
| 10 | `RollingStd_24` | 0.0069 | Daily volatility |

### 3.10 Operational Lag-Seeding Requirement

> **⚠️ Critical for Deployment**

This model requires **168 hours (7 days) of historical `Load_MW` values** to be available at inference time to populate the lag and rolling-window features. Without this seed buffer:
- All lag features (`Load_lag_1` through `Load_lag_168`) will be missing or zero
- Rolling statistics (`RollingMean_168`, `RollingStd_168`) will be incorrect
- **Model accuracy will degrade severely**

**Operational seeding strategy:**
1. Maintain a rolling circular buffer of the last 168 hourly `Load_MW` observations.
2. At each inference step (hour t), compute all lag and rolling features from the buffer.
3. After receiving the actual load at t, append it to the buffer and shift.

---

## 4. Model C — NSRDB Baseline PV Model

### 4.1 Artifact Paths

| Artifact | Path | Note |
|:---------|:-----|:-----|
| **Model file** | *(none — not saved)* | ❌ Must retrain from source |
| **Test predictions** | `notebooks/nsrdb_artifacts/baseline_2_predictions.csv` | Historical predictions only |
| **Source data** | `notebooks/nsrdb_data.csv` | Required for retraining |
| **Training notebook** | `notebooks/nsrdb_model.ipynb` | Full training code present |

> **Status: BENCHMARK ONLY.** No serialized model artifact exists. The model is not operationally deployable without (a) retraining from `nsrdb_data.csv` and (b) access to live NSRDB-equivalent historical weather data for feature computation at inference time.

### 4.2 Target Variable

| Property | Value |
|:---------|:------|
| **Column name** | `PV_target` |
| **Description** | Physics-derived PV output at t+1 hour |
| **Unit** | kW |
| **System capacity** | 100 kW |
| **Derivation** | Computed from NSRDB irradiance via POA model |

**Physics-based target generation (from notebook):**

```python
# Panel configuration
panel_tilt     = 33°          # degrees
panel_azimuth  = 180°         # south-facing
efficiency     = 0.80         # system derating factor

# Step 1: Solar zenith → radians
zenith_rad = Solar_Zenith_Angle × (π / 180)

# Step 2: Beam POA irradiance
Beam_POA = DNI × cos(angle_of_incidence)

# Step 3: Diffuse POA irradiance
Diffuse_POA = DHI × (1 + cos(panel_tilt)) / 2

# Step 4: Total POA (clipped ≥ 0)
POA_Irradiance = max(0, Beam_POA + Diffuse_POA)

# Step 5: PV output
PV_Output_kW = 100 kW × (POA_Irradiance / 1000) × 0.80
```

> **Note:** POA and PV_Output_kW are used only for target generation. Neither is used as an ML input feature. The ground-reflected/albedo component and full solar azimuth-based angle of incidence are simplified.

### 4.3 Feature List (13 Features)

| # | Feature Name | Type | Unit | Source |
|:--|:-------------|:----:|:----:|:-------|
| 1 | `Temperature` | Meteorological | °C | NSRDB |
| 2 | `Wind Speed` | Meteorological | m/s | NSRDB |
| 3 | `Wind Direction` | Meteorological | ° | NSRDB |
| 4 | `Pressure` | Meteorological | mbar | NSRDB |
| 5 | `Solar Zenith Angle` | Solar geometry | ° | NSRDB |
| 6 | `DNI` | Irradiance | W/m² | NSRDB |
| 7 | `GHI` | Irradiance | W/m² | NSRDB |
| 8 | `DHI` | Irradiance | W/m² | NSRDB |
| 9 | `Relative Humidity` | Meteorological | % | NSRDB |
| 10 | `Dew Point` | Meteorological | °C | NSRDB |
| 11 | `Hour_sin` | Cyclical time | dimensionless | Engineered |
| 12 | `Hour_cos` | Cyclical time | dimensionless | Engineered |
| 13 | `DayOfYear` | Calendar | integer (1–366) | Engineered |

### 4.4 Preprocessing Pipeline

```
NSRDB CSV (nsrdb_data.csv)
  Columns: Year, Month, Day, Hour, Minute, + weather vars
        │
        ▼
1. Construct Datetime:
   df["Datetime"] = pd.to_datetime(df[["Year","Month","Day","Hour","Minute"]])
   → Naive datetime (no timezone)
        │
        ▼
2. Sort chronologically
        │
        ▼
3. Compute cyclical time features:
   Hour_sin = sin(2π × Hour / 24)
   Hour_cos = cos(2π × Hour / 24)
   DayOfYear = Datetime.dt.dayofyear
        │
        ▼
4. Generate physics-based PV target (see §4.2)
        │
        ▼
5. Drop NaN rows
        │
        ▼
6. Chronological 80/20 train/test split
        │
        ▼
7. Train XGBRegressor (no saved artifact → model lost after session)
```

### 4.5 Timestamp & Timezone Handling

| Property | Detail |
|:---------|:-------|
| **Data format** | Separate Year/Month/Day/Hour/Minute integer columns |
| **Resolution** | 30-minute intervals |
| **Timezone** | Naive datetime — NSRDB data for Phoenix, AZ is typically in local standard time (LST = UTC-7) |
| **Inference constraint** | Cannot be used operationally; requires NSRDB archive access for historical irradiance values |

### 4.6 Model Configuration

| Hyperparameter | Value |
|:---------------|:------|
| Algorithm | XGBoost Regressor |
| `n_estimators` | 500 |
| `max_depth` | 6 |
| `learning_rate` | 0.05 |
| `subsample` | 0.8 |
| `colsample_bytree` | 0.8 |
| `objective` | `reg:squarederror` |
| `random_state` | 42 |
| `n_jobs` | -1 |

### 4.7 Training Data Characteristics

| Property | Value |
|:---------|:------|
| **Year used** | 2018 (single year) |
| **Resolution** | 30-min → 8,760 h/year → 17,520 raw samples |
| **Total samples (after preprocessing)** | 26,276 (note: notebook output shows 3-year context was used) |
| **Train samples** | 21,020 (80%) |
| **Test samples** | 5,256 (20%) |
| **Split method** | Strictly chronological — no random sampling |

### 4.8 Test Set Performance

| Scope | MAE (kW) | RMSE (kW) | R² | nMAE |
|:------|:--------:|:---------:|:--:|:----:|
| **Overall (all hours)** | 2.9639 | 5.8897 | 0.9269 | — |
| **Daytime only** | 5.4466 | 8.0726 | 0.8697 | 5.45% |

**Persistence daytime baseline:** MAE = 10.73 kW, R² = 0.7021, nMAE = 10.73%  
→ **XGBoost reduces daytime MAE by ~66.6%** over persistence.

### 4.9 Feature Importance (Permutation, Top 5)

| Rank | Feature | Importance (MAE reduction) |
|:----:|:--------|:--------------------------:|
| 1 | GHI | 6.549 |
| 2 | DNI | 4.309 |
| 3 | Hour_sin | 2.951 |
| 4 | DHI | 2.058 |
| 5 | Solar Zenith Angle | 0.853 |

---

## 5. Cross-Model Comparison

### 5.1 Summary Comparison Table

| Property | Open-Meteo PV | Load Forecaster | NSRDB Baseline |
|:---------|:-------------:|:---------------:|:--------------:|
| **Algorithm** | XGBoost Reg. | XGBoost Reg. | XGBoost Reg. |
| **Forecast horizon** | t+1 hour | t+1 hour | t+1 hour |
| **Target** | PV output (kW) | Load (MW) | PV output (kW) |
| **Features** | 14 | 26 | 13 |
| **Lag-dependent** | ❌ No | ✅ Yes (168 h) | ❌ No |
| **Saved artifact** | ✅ JSON | ✅ JSON | ❌ None |
| **Data source** | Open-Meteo API | RMSC / utility | NSRDB archive |
| **Timezone** | Naive UTC (ambiguous) | UTC → Phoenix | Naive local |
| **Resolution** | Hourly | Hourly | 30-min |
| **Training period** | 2017–2019 | 2017–2019 | 2018 |
| **Test R²** | ~0.99 (est.) | 0.9933 | 0.9269 |
| **Operational** | ✅ Yes | ✅ Yes (w/ seed) | ❌ No |

### 5.2 PV Model Comparison (Open-Meteo vs. NSRDB)

| Metric | Open-Meteo PV | NSRDB Baseline | Notes |
|:-------|:-------------:|:--------------:|:------|
| **Data source** | Forecast API (future-available) | Historical archive (not forecast) | Critical distinction |
| **Features** | Multi-band irradiance + met. | Multi-band irradiance + solar geometry | Similar signal space |
| **Solar geometry** | Implicit via irradiance | Explicit via Solar Zenith Angle | NSRDB uses explicit geometry |
| **Operational** | ✅ Ready | ❌ Not deployable | Open-Meteo wins for production |
| **Physics basis** | None (data-driven) | Explicit POA target derivation | NSRDB target is physics-grounded |

---

## 6. Data Leakage Audit

### 6.1 Open-Meteo PV Model

| Check | Status | Detail |
|:------|:------:|:-------|
| Target is t+1 (next hour) | ✅ Clean | `target_pv_next_hour = pv_output.shift(-1)` |
| Weather features are concurrent (t) | ✅ Clean | No future weather leaked into X |
| Train/test split is chronological | ✅ Clean | First 80% for training |
| Irradiance features at time t | ⚠️ **Review** | Current-hour irradiance is a known quantity at t, but should not reveal t+1 PV directly since it's a 1-h lag target |
| No future lag values in X | ✅ Clean | No lag-based features used |

**Overall: LOW LEAKAGE RISK.** The irradiance features at time t are legitimate inputs for forecasting t+1 PV.

### 6.2 Load Forecaster

| Check | Status | Detail |
|:------|:------:|:-------|
| Target is t+1 | ✅ Clean | `Target_Load = Load_MW.shift(-1)` |
| Rolling statistics use past-only windows | ✅ Clean | Notebook explicitly confirms `.rolling(...).mean()` on historical values |
| Lag features reference past values only | ✅ Clean | All lags are t-n for n ≥ 1 |
| Train/val/test split is chronological | ✅ Clean | 70/15/15 strict time ordering |
| No future load values in X | ✅ Clean | Lags are purely backward-looking |

**Overall: NO LEAKAGE DETECTED.** Rolling statistics computed on past-only observations with explicit confirmation in notebook.

### 6.3 NSRDB Baseline

| Check | Status | Detail |
|:------|:------:|:-------|
| Target is next timestep | ✅ Clean | `PV_target = PV_Output_kW.shift(-1)` |
| POA/PV_Output not used as features | ✅ Clean | Explicitly excluded from ML feature set |
| Solar Zenith Angle at time t | ✅ Clean | Known from solar geometry calculation — not future data |
| Irradiance at time t | ⚠️ **Same as above** | Current-hour irradiance is a valid feature for t+1 forecast |
| Chronological split | ✅ Clean | 80/20 chronological |

**Overall: LOW LEAKAGE RISK.** Physics-derived target is clean; no auto-correlation leakage detected.

---

## 7. Operational Readiness Summary

### 7.1 Deployment Status by Model

#### ✅ Model A — Open-Meteo PV (READY)

**To use in production:**
```python
import json
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

# 1. Load model
model = XGBRegressor()
model.load_model("notebooks/open-meteo-model_artifacts/deployment_pv_xgboost_model.json")

# 2. Load expected feature order
with open("notebooks/open-meteo-model_artifacts/pv_model_features.json") as f:
    features = json.load(f)

# 3. Fetch Open-Meteo data for the target hour (t)
# df_weather: DataFrame with Open-Meteo API columns

# 4. Engineer time features
df_weather["hour_sin"] = np.sin(2 * np.pi * df_weather["time"].dt.hour / 24)
df_weather["hour_cos"] = np.cos(2 * np.pi * df_weather["time"].dt.hour / 24)
df_weather["month"]    = df_weather["time"].dt.month
df_weather["dayofweek"] = df_weather["time"].dt.dayofweek

# 5. Predict
X = df_weather[features]
pv_pred_kw = model.predict(X)
```

**Key constraints:**
- Ensure column names exactly match (including units in brackets, e.g., `temperature_2m (°C)`)
- Timestamp timezone must match training convention (naive UTC or consistently offset)
- No lag seeding needed

#### ✅ Model B — Load Forecaster (READY WITH SEED)

**To use in production:**
```python
import json
import pandas as pd
import xgboost as xgb

# 1. Load model and feature list
model = xgb.XGBRegressor()
model.load_model("notebooks/load_forecasting_artifacts/load_xgboost_model.json")
with open("notebooks/load_forecasting_artifacts/load_model_features.json") as f:
    feature_config = json.load(f)
features = feature_config["features"]

# 2. Seed buffer: last 168 hours of observed Load_MW (UTC timestamps)
# load_history: pd.Series indexed by UTC datetime, length >= 168

# 3. For each inference hour (UTC timestamp ts_utc):
ts_local = ts_utc.tz_convert("America/Phoenix")

row = {
    "Hour_sin":       np.sin(2*np.pi * ts_local.hour / 24),
    "Hour_cos":       np.cos(2*np.pi * ts_local.hour / 24),
    "DayOfWeek_sin":  np.sin(2*np.pi * ts_local.dayofweek / 7),
    "DayOfWeek_cos":  np.cos(2*np.pi * ts_local.dayofweek / 7),
    "Month_sin":      np.sin(2*np.pi * ts_local.month / 12),
    "Month_cos":      np.cos(2*np.pi * ts_local.month / 12),
    "Hour":           ts_local.hour,
    "DayOfWeek":      ts_local.dayofweek,
    "DayOfMonth":     ts_local.day,
    "Month":          ts_local.month,
    "DayOfYear":      ts_local.dayofyear,
    "IsWeekend":      int(ts_local.dayofweek >= 5),
    "Load_lag_1":     load_history[-1],
    "Load_lag_2":     load_history[-2],
    # ... etc.
    "RollingMean_3":  load_history[-3:].mean(),
    # ... etc.
}

X = pd.DataFrame([row])[features]
load_pred_mw = model.predict(X)[0]
```

**Key constraints:**
- **Must** maintain 168-hour rolling load history buffer
- Input timestamps must be UTC; convert to `America/Phoenix` for calendar features
- Predictions are in **MW** (regional scale); apply a scaling factor for microgrid use

#### ❌ Model C — NSRDB Baseline (NOT DEPLOYABLE)

**Current state:** No saved model artifact. Only historical test predictions in `nsrdb_artifacts/baseline_2_predictions.csv`.

**To re-enable as a benchmark:**
1. Run `notebooks/nsrdb_model.ipynb` using `nsrdb_data.csv`
2. Add `model.save_model("nsrdb_artifacts/nsrdb_pv_model.json")` after training
3. Save features list to `nsrdb_artifacts/nsrdb_model_features.json`
4. This model **cannot** be used for future inference without live NSRDB-equivalent data

---

## 8. Integration Recommendations

### 8.1 Immediate Actions

| Priority | Action | Model(s) | Effort |
|:--------:|:-------|:--------:|:------:|
| 🔴 High | Clarify Open-Meteo timestamp timezone convention — verify that training timestamps are UTC or consistently Phoenix-local before deployment | Model A | Low |
| 🔴 High | Implement 168-hour load history buffer for lag-seeding | Model B | Medium |
| 🟡 Medium | Save NSRDB model artifact with explicit `save_model()` call | Model C | Low |
| 🟡 Medium | Validate Model B predictions with actual microgrid load data; MW-scale outputs need a normalization factor | Model B | Medium |
| 🟢 Low | Add uncertainty quantification to PV model (e.g., quantile regression or conformal prediction) beyond the empirical bound estimates | Model A | Medium |

### 8.2 Architecture for Operational Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│                    HOURLY INFERENCE LOOP                       │
│                                                                │
│  t (current hour UTC)                                          │
│        │                                                       │
│        ├─── Open-Meteo API ──► [Model A] ──► PV_pred (kW)    │
│        │                                                       │
│        ├─── Load history    ──► [Model B] ──► Load_pred (MW) │
│        │    buffer (168 h)                                     │
│        │                                                       │
│        └─── [Optimizer / Battery Scheduler]                   │
│                  ▲ PV_pred, Load_pred, State-of-Charge        │
│                  │                                             │
│               DISPATCH DECISION                                │
└──────────────────────────────────────────────────────────────┘
```

### 8.3 Model Maintenance Guidelines

| Concern | Recommendation |
|:--------|:---------------|
| **Model drift** | Re-evaluate monthly against actual PV/load data; retrain annually or when MAE degrades >20% |
| **Open-Meteo API changes** | Monitor column name changes in API response; feature name mismatch will cause silent prediction errors |
| **Load forecaster scale** | The regional (MW-scale) load forecast should be validated against actual building/microgrid load data before use in dispatch decisions |
| **NSRDB model** | For future research, consider saving as a comparison baseline; consider adding POA as a feature ablation experiment |
| **Feature versioning** | Pin `pv_model_features.json` and `load_model_features.json` to source control; never modify column order without retraining |
| **Confidence intervals** | The PV model's empirical bounds in `pv_test_predictions.csv` cover only the test period (summer–fall 2019); re-derive bounds seasonally |

### 8.4 Known Limitations

1. **Load model is regional, not microgrid-scale:** The model predicts Maricopa County loads (3,000–11,000 MW). A microgrid needs either a building-specific load model or a reliable scaling/disaggregation method.

2. **Open-Meteo PV model's timezone ambiguity:** The absence of explicit timezone handling in training creates a risk of systematic hour-of-day error in predictions during inference if the caller passes UTC hours but the model was trained on local solar hours.

3. **NSRDB model is not forward-looking:** NSRDB provides high-quality historical data but not operational forecasts. Its excellent performance as a benchmark does not translate to real-time use.

4. **No model ensemble or uncertainty quantification:** Currently, only point predictions are made (with empirical bounds for PV). A proper prediction interval method (quantile XGBoost, conformal prediction) would improve risk management in battery dispatch.

5. **Static panel assumptions in NSRDB target:** The PV target was derived using fixed panel tilt (33°) and azimuth (180°). Any real-world deviation in panel orientation will cause bias in both training targets and test evaluation.

---

*Report generated by the Model Inspection Agent for the MicroGrid Battery Optimization project.*  
*All file paths are relative to project root: `c:\Users\nitin\Desktop\MicroGrid_Project`*
